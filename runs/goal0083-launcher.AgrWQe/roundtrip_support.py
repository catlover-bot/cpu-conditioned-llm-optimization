#!/usr/bin/env python3
"""コード生成実験用の未変更C/LLVM IRと、ローカル往復確認を作る。

対象: 保存済みPolyBench 4.2.1-beta 30カーネル×3サイズ。
計算関数へ位置表示命令を挿入しない。マクロ展開した関数本文を保存し、
初期化・出力・mainを別コンパイル単位に隔離する。完全なLLVMモジュールを
保存し、必要な宣言・意味属性・メタデータは削らない。
本スクリプトは元の信頼済みカーネルだけを実行する。LLM生成物を受け付けない。
公式初期値の出力往復試験であり、全入力同値証明・生成物用検証器ではない。
API送信・性能測定・Git操作・元ファイル上書きなし。
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone

CANDIDATE_SHA = 'a6c6423984aab7a26f90b86aab36ab3962fd208fb6f977ad068b80d4fc31c7a1'
INTAKE = 'runs/goal0041-dataset-intake/20260910T132522.441454Z-69857bdb'
SIZE_MACROS = {'MINI':'MINI_DATASET','SMALL':'SMALL_DATASET','MEDIUM':'MEDIUM_DATASET'}
TARGET = ['--target=x86_64-unknown-linux-gnu', '-march=x86-64', '-mtune=generic']
CFLAGS = ['-std=gnu11', '-fno-fast-math', '-ffp-contract=off', '-fno-lto', *TARGET]
IRFLAGS = ['-fno-fast-math', '-ffp-contract=off', '-fno-lto', *TARGET]

class BuildError(RuntimeError): pass

def require(ok, message):
    if not ok: raise BuildError(message)

def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def unique(pairs):
    out={}
    for k,v in pairs:
        require(k not in out, 'JSONキー重複: '+k); out[k]=v
    return out

def parse_json(data):
    def bad(x): raise BuildError('不正なJSON数値: '+x)
    return json.loads(data, object_pairs_hook=unique, parse_constant=bad)

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str): data=data.encode('utf-8')
    with path.open('xb') as f: f.write(data)

def jwrite(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def safe_file(root, rel):
    q=PurePosixPath(rel)
    require(q.parts and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,
            '不正な相対パス: '+rel)
    p=root/Path(*q.parts)
    require(p.is_file() and root.resolve() in p.resolve().parents, '入力がありません: '+str(p))
    cur=p
    while cur!=root:
        require(not cur.is_symlink(), 'シンボリックリンクを拒否: '+str(cur)); cur=cur.parent
    return p

def mask_noncode(text):
    # 文字位置と改行を保ち、コメント・文字列だけを空白にする。
    out=list(text); i=0
    while i<len(text):
        if text.startswith('//',i):
            end=text.find('\n',i+2); end=len(text) if end<0 else end
        elif text.startswith('/*',i):
            end=text.find('*/',i+2); require(end>=0,'閉じていないコメント'); end+=2
        elif text[i] in '\"\'':
            q=text[i]; end=i+1
            while end<len(text):
                if text[end]=='\\': end+=2; continue
                if text[end]==q: end+=1; break
                end+=1
            else: raise BuildError('閉じていない文字列')
        else: i+=1; continue
        for j in range(i,min(end,len(text))):
            if out[j]!='\n': out[j]=' '
        i=end
    return ''.join(out)

def matching(s, i, a, b):
    require(i>=0 and s[i]==a,'対応括弧の開始位置が不正')
    n=0
    for j in range(i,len(s)):
        if s[j]==a: n+=1
        if s[j]==b:
            n-=1
            if n==0: return j
    raise BuildError('対応括弧がありません')

def function_span(s, name):
    m=mask_noncode(s); hits=[]
    for x in re.finditer(r'\b(?:static\s+)?void\s+'+re.escape(name)+r'\s*\(',m):
        opening=m.index('(',x.start()); closing=matching(m,opening,'(',')')
        p=closing+1
        while p<len(m) and m[p].isspace(): p+=1
        if p<len(m) and m[p]=='{': hits.append((x.start(),matching(m,p,'{','}')+1))
    require(len(hits)==1,f'{name}: 関数定義が一意でない: {len(hits)}')
    return hits[0]

def body(s, name):
    a,b=function_span(s,name); fn=s[a:b]; m=mask_noncode(fn)
    return fn[m.index('{'):]

def external_function(fn):
    # static以外は本文も署名も変更しない。
    return re.sub(r'^static\s+', '', fn, count=1)

def split_args(s):
    m=mask_noncode(s); stack=[]; out=[]; start=0
    for i,c in enumerate(m):
        if c in '([{': stack.append(c)
        elif c in ')]}':
            require(bool(stack),'引数の括弧不整合'); stack.pop()
        elif c==',' and not stack: out.append(s[start:i].strip()); start=i+1
    require(not stack,'引数の括弧不整合'); out.append(s[start:].strip()); return out

def raw_print_source(s):
    a,b=function_span(s,'print_array'); fn=s[a:b]; m=mask_noncode(fn); sites=[]
    for x in re.finditer(r'\bfprintf\s*\(',m):
        o=m.index('(',x.start()); e=matching(m,o,'(',')'); end=e+1
        while end<len(m) and m[end].isspace(): end+=1
        require(end<len(m) and m[end]==';','出力文の構文不整合')
        args=split_args(fn[o+1:e])
        if len(args)==3 and re.sub(r'\s+','',args[0])=='POLYBENCH_DUMP_TARGET' and re.sub(r'\s+','',args[1])=='DATA_PRINTF_MODIFIER':
            sites.append((x.start(),end+1,args[2]))
    require(bool(sites),'公式の配列出力が見つかりません')
    for p,q,expr in reversed(sites):
        stmt=('do { __typeof__('+expr+') cpucond_value = ('+expr+'); '
              'if (fwrite(&cpucond_value, 1, sizeof(cpucond_value), stdout) != sizeof(cpucond_value)) exit(91); } while (0);')
        fn=fn[:p]+stmt+fn[q:]
    fn=fn[:-1]+'\n  if (fflush(stdout) != 0) exit(92);\n}'
    return '#include <stdio.h>\n#include <stdlib.h>\n'+s[:a]+fn+s[b:],len(sites)

def local_typedefs(original, preprocessed):
    # PolyBenchのソース内型定義を、展開後の宣言として残す（例: nussinovのbase）。
    names=[]
    for x in re.finditer(r'\btypedef\s+[^;{}]+;',mask_noncode(original)):
        ns=re.findall(r'[A-Za-z_]\w*',x.group()); names.append(ns[-1])
    decls=[]
    for n in sorted(set(names)):
        matches=list(re.finditer(r'\btypedef\s+[^;{}]*\b'+re.escape(n)+r'\s*;',mask_noncode(preprocessed)))
        require(len(matches)==1,'型宣言が一意でない: '+n)
        x=matches[0]; decls.append(preprocessed[x.start():x.end()])
    return '\n'.join(decls)+'\n' if decls else ''

def isolate(raw_pp, name, typedefs=''):
    a,b=function_span(raw_pp,name); fn=external_function(raw_pp[a:b]); m=mask_noncode(fn)
    header=fn[:m.index('{')].rstrip()
    kernel='#include <math.h>\n#include <stdint.h>\n#include <stddef.h>\n'+typedefs+'\n__attribute__((noinline)) '+fn+'\n'
    driver=raw_pp[:a]+header+';\n'+raw_pp[b:]
    require(body(raw_pp,name)==body(kernel,name),'抽出によって関数本文が変更された')
    return kernel,driver

def sanitize_ir(ir):
    # 実CPUの属性だけを除く。宣言や数値意味属性は削除しない。
    ir=re.sub(r'^; ModuleID = .*$', "; ModuleID = 'kernel.c'", ir, flags=re.M)
    ir=re.sub(r'^source_filename = .*$', 'source_filename = "kernel.c"',ir,flags=re.M)
    ir=re.sub(r'\s+"(?:target-cpu|target-features|tune-cpu)"="[^"\n]*"','',ir)
    require(not re.search(r'\b(?:haswell|znver\d*|epyc)\b',ir,re.I),'実CPU名が中間表現に残っています')
    require('target-cpu' not in ir and 'target-features' not in ir and 'tune-cpu' not in ir,'対象CPU属性が残っています')
    return ir

def root_function(data,name):
    decoder=json.JSONDecoder(); roots=[]; pos=0
    while pos<len(data):
        while pos<len(data) and data[pos].isspace(): pos+=1
        if pos==len(data): break
        obj,pos=decoder.raw_decode(data,pos); roots.append(obj)
    found=[]
    def walk(n):
        if not isinstance(n,dict): return
        if n.get('kind')=='FunctionDecl' and n.get('name')==name and any(x.get('kind')=='CompoundStmt' for x in n.get('inner',[])):
            found.append(n); return
        for c in n.get('inner',[]): walk(c)
    for r in roots: walk(r)
    require(len(found)==1,name+': 構文木の定義が一意でない'); return found[0]

def loop_tree(fn):
    out=[]; controls=0
    def walk(n,parents,ctx):
        nonlocal controls
        if not isinstance(n,dict): return
        k=n.get('kind'); children=n.get('inner',[])
        if k=='ForStmt':
            idx=len(out); out.append([idx,list(parents),list(ctx),children[-1].get('kind')]); parents=(*parents,idx)
        cid=None
        if k in {'ForStmt','WhileStmt','DoStmt','IfStmt','SwitchStmt'}: cid=controls; controls+=1
        for i,c in enumerate(children): walk(c,parents,ctx if cid is None else (*ctx,(k,cid,i)))
    walk(fn,(),()); return out

def run(argv, stem, timeout=120, cwd=None):
    # 不要なAPIキー・資格情報は子プロセスへ渡さず、実験では元コードのみ実行する。
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LC_ALL':'C','HOME':str(stem.parent)}
    try:
        p=subprocess.run([str(a) for a in argv],capture_output=True,timeout=timeout,cwd=cwd,env=env)
        rc=p.returncode; so=p.stdout; se=p.stderr; state='completed'
    except subprocess.TimeoutExpired as e:
        rc=None; so=e.stdout or b''; se=e.stderr or b''; state='timeout'
    write(stem.with_suffix('.stdout'),so); write(stem.with_suffix('.stderr'),se)
    jwrite(stem.with_suffix('.command.json'),{'argv':[str(a) for a in argv], 'cwd':str(cwd) if cwd else None,
       'state':state,'returncode':rc,'stdout_sha256':sha(so),'stderr_sha256':sha(se)})
    require(rc==0 and state=='completed',f'コマンド失敗: {stem.with_suffix(".stderr")}')
    return so

def ast_tree(clang,path,name,flags,stem):
    d=run([clang,*flags,'-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter','-Xclang',name,path],stem)
    return loop_tree(root_function(d.decode('utf-8'),name))

def exact(a,b): return bool(a) and len(a)==len(b) and a==b

def materialize(raw_pp, name, typedefs, out, clang, util=None, expected_loops=None):
    out.mkdir(parents=True, exist_ok=False)
    inputs=out/'inputs'; work=out/'check'; inputs.mkdir(); work.mkdir()
    kernel,driver=isolate(raw_pp,name,typedefs)
    a0,_=function_span(raw_pp,name)
    reference_pp=raw_pp[:a0]+'__attribute__((noinline)) '+raw_pp[a0:]
    require(body(raw_pp,name)==body(reference_pp,name),'noinline境界指定で本文が変わりました')
    write(inputs/'kernel.c',kernel); write(work/'reference.c',reference_pp); write(work/'driver.c',driver)
    a=ast_tree(clang,work/'reference.c',name,CFLAGS,work/'ast-reference')
    b=ast_tree(clang,inputs/'kernel.c',name,CFLAGS,work/'ast-isolated')
    require(a==b,name+': ループ構造が変わっています')
    if expected_loops is not None: require(len(a)==expected_loops,name+': ループ数不一致')
    jwrite(work/'loop-structure.json',{'original':a,'isolated':b,'equal':True})
    raw_ir=run([clang,*CFLAGS,'-O0','-Xclang','-disable-O0-optnone','-fno-discard-value-names','-S','-emit-llvm',
                'kernel.c','-o','-'],work/'emit-ir',cwd=inputs).decode('utf-8')
    ir=sanitize_ir(raw_ir)
    defs=re.findall(r'^define\b[^\n]*@([A-Za-z_][\w.]*)\(',ir,re.M)
    require(defs==[name],name+': IRに余分な定義または関数欠落')
    require('optnone' not in ir,'中間表現の最適化禁止属性が残っています')
    require('CPUCOND_LOOP_' not in ir,'旧位置表示命令が残っています')
    write(inputs/'kernel.ll',ir)
    # 完全なモジュールとして読み込み直す。宣言/属性定義を切り落とさない。
    run([clang,*IRFLAGS,'-x','ir','-O0','-emit-llvm','-c',inputs/'kernel.ll','-o',work/'parsed.bc'],work/'parse-ir')
    deps=[util] if util else []
    run([clang,*CFLAGS,'-O0','-c',work/'driver.c','-o',work/'driver.o'],work/'compile-driver')
    outputs={}
    for level in ('O0','O3'):
        ref=work/f'reference-{level}'
        run([clang,*CFLAGS,'-'+level,work/'reference.c',*deps,'-lm','-o',ref],work/f'build-reference-{level}')
        outputs[f'reference-{level}']=run([ref],work/f'run-reference-{level}')
        for form,flags in [('C',CFLAGS),('IR',IRFLAGS)]:
            obj=work/f'kernel-{form}-{level}.o'; src=inputs/('kernel.c' if form=='C' else 'kernel.ll')
            run([clang,*flags,'-'+level,'-c',src,'-o',obj],work/f'compile-{form}-{level}')
            exe=work/f'program-{form}-{level}'
            run([clang,*IRFLAGS,work/'driver.o',obj,*deps,'-lm','-o',exe],work/f'link-{form}-{level}')
            outputs[f'{form}-{level}']=run([exe],work/f'run-{form}-{level}')
    oracle=outputs['reference-O0']; require(bool(oracle),name+': 参照出力が空です')
    comparisons={k:exact(oracle,v) for k,v in outputs.items()}
    bad=bytearray(oracle); bad[len(bad)//2]^=1
    require(not exact(oracle,bytes(bad)),'比較器が改変出力を受け入れました')
    result={'function':name,'loop_count':len(a),'kernel_body_preserved_after_preprocessing':True,
        'loop_structure_equal':True,'standalone_ir_compiled':True,'outputs_equal':comparisons,
        'output_bytes':len(oracle),'output_sha256':sha(oracle),'negative_output_control_rejected':True,
        'correctness_executions':len(outputs),'timing_measurements':0,
        'passed':all(comparisons.values()),'formal_equivalence_proven':False,
        'arbitrary_generated_code_gate_ready':False,'api_submission_authorized':False}
    jwrite(out/'instance-result.json',result)
    require(result['passed'],name+': 未変更版の往復結果が一致しません')
    return result

def pick_clang(requested=None, strict=True):
    options=[requested] if requested else ['clang-18','clang']
    for opt in options:
        p=shutil.which(opt) if opt else None
        if not p: continue
        v=subprocess.check_output([p,'--version'],text=True,timeout=10).splitlines()[0]
        if not strict or re.search(r'clang version 18\.1\.3\b',v): return p,v
    raise BuildError('Clang 18.1.3が必要です。clang --version の出力を共有してください。自動インストールはしません。')

def snapshot(root):
    result={}
    if not root.exists(): return result
    require(not root.is_symlink(),'入力ディレクトリがリンクです')
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'リンクを含む入力を拒否: '+str(p))
        if p.is_file(): result[p.relative_to(root).as_posix()]=file_sha(p)
    return result

def execute(repo,clang,version):
    repo=repo.resolve(); manifest=safe_file(repo,'configs/final-candidate-manifest-v1.json')
    require(file_sha(manifest)==CANDIDATE_SHA,'既存候補manifestのハッシュ不一致')
    entries=parse_json(manifest.read_bytes())['kernels']
    require(len(entries)==30 and len({e['kernel_id'] for e in entries})==30,'元カーネルが30件ではありません')
    intake=repo/INTAKE; pb=intake/'upstream/polybench-c-4.2.1-beta'
    catalog_path=safe_file(repo,INTAKE+'/polybench-catalog.json')
    cats={x['id']:x for x in parse_json(catalog_path.read_bytes())}
    input_roots={'polybench':pb,'previous_corpus':repo/'generated/llm-input-corpus-v1',
                 'previous_prompts':repo/'generated/final-llm-prompts-v1'}
    before={k:snapshot(p) for k,p in input_roots.items()}
    for e in entries:
        kid=e['kernel_id']; require(kid in cats,'カタログに課題がありません: '+kid)
        p=safe_file(pb,cats[kid]['source'])
        require(file_sha(p)==e['source_sha256']==cats[kid]['source_sha256'],'元Cのハッシュ不一致: '+kid)
        hp=safe_file(pb,cats[kid]['header'])
        require(file_sha(hp)==cats[kid]['header_sha256'],'元ヘッダのハッシュ不一致: '+kid)
    runid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    out=repo/'runs'/'goal0062-codegen-roundtrip'/runid; out.mkdir(parents=True,exist_ok=False)
    write(out/'tool-source.py',Path(__file__).read_bytes())
    jwrite(out/'input-snapshots.json',before)
    jwrite(out/'provenance.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'compiler':version,
      'script_sha256':file_sha(Path(__file__)),'candidate_manifest_sha256':file_sha(manifest),
      'catalog_sha256':file_sha(catalog_path),'c_flags':CFLAGS,'common_target':'x86_64-unknown-linux-gnu / x86-64 / generic',
      'no_actual_cpu_model_in_input':True,'noinline_kernel_boundary':True,'task':'code_generation_not_candidate_selection',
      'api_calls':0,'network_requests':0,'performance_measurements':0})
    if (pb/'LICENSE.txt').is_file(): write(out/'source-license.txt',(pb/'LICENSE.txt').read_bytes())
    rows=[]; failure=None
    try:
        util=out/'polybench.o'
        run([clang,*CFLAGS,'-O0','-I',pb/'utilities','-c',pb/'utilities/polybench.c','-o',util],out/'compile-utility')
        for e in entries:
            kid=e['kernel_id']; src=pb/cats[kid]['source']; orig=src.read_text(encoding='utf-8'); name=e['function_name']
            raw,sites=raw_print_source(orig)
            require(body(orig,name)==body(raw,name),kid+': 出力計測挿入で計算本文が変更されました')
            for size,macro in SIZE_MACROS.items():
                prep=out/'preprocess'/kid/size; prep.mkdir(parents=True,exist_ok=False)
                write(prep/'raw.c',raw)
                flags=[*CFLAGS,f'-D{macro}','-DPOLYBENCH_USE_C99_PROTO','-DPOLYBENCH_DUMP_ARRAYS',
                       '-I',pb/'utilities','-I',src.parent]
                pp=run([clang,*flags,'-E','-P',prep/'raw.c'],prep/'preprocess').decode('utf-8')
                result=materialize(pp,name,local_typedefs(orig,pp),out/'cases'/kid/size,clang,util,e['syntactic_loop_count'])
                result.update({'kernel':kid,'size':size,'source_sha256':e['source_sha256'],'output_sites':sites,
                               'c_input':f'cases/{kid}/{size}/inputs/kernel.c',
                               'ir_input':f'cases/{kid}/{size}/inputs/kernel.ll'})
                rows.append(result)
                print(f'{kid:16s} {size:6s} 計算本文=保存 ループ構造=一致 IR単体=成功 出力6経路=一致',flush=True)
    except Exception as exc:
        failure=f'{type(exc).__name__}: {exc}'
    unchanged={k:snapshot(p)==before[k] for k,p in input_roots.items()}
    require(file_sha(manifest)==CANDIDATE_SHA,'処理中にmanifestが変化しました')
    passed=len(rows)==90 and all(unchanged.values()) and failure is None
    summary={'completion':'CODEGEN_ROUNDTRIP_COMPLETE' if passed else 'CODEGEN_ROUNDTRIP_BLOCKED',
      'instances_planned':90,'instances_passed':len(rows),'c_documents':len(rows),'ir_documents':len(rows),
      'old_inputs_and_source_unchanged':unchanged,'failure':failure,'run_directory':str(out),
      'scope':'unmodified_reference_official_initializer_live_out_roundtrip_only',
      'api_calls':0,'performance_measurements':0,'formal_equivalence_proven':False,
      'generated_candidate_validator_ready':False,'api_submission_authorized':False}
    jwrite(out/'manifest.json',{'corpus_id':'codegen-input-roundtrip-v1','summary':summary,'rows':rows})
    jwrite(out/'summary.json',summary)
    files=snapshot(out)
    write(out/'SHA256SUMS',''.join(f'{h}  {p}\n' for p,h in files.items()))
    print('\n=== コード生成用入力の往復確認 ===')
    print(f'合格した条件: {len(rows)}/90')
    print('元のC・既存入力の変更: '+('なし' if all(unchanged.values()) else 'あり'))
    print('API送信: なし。速度の測定: なし。生成物用の多入力検証器: 次段階。')
    print(summary['completion']); print('保存先:',out)
    if failure: print('停止理由:',failure)
    return 0 if passed else 1

# 外部モデルも元データも使わない合成試験。
FIXTURE=r'''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
typedef char base;
static void kernel_fixture(int n, int m, double *a, base *seq) {
 int i,j;
 for(i=0;i<n;i++)
  for(j=0;j<m;j++)
   if(j>=1) a[i*m+j] = a[i*m+j]+sqrt((double)seq[j]);
}
int main(void){
 double a[6]={-0.0,1.0,2.0,3.0,4.0,5.0}; base seq[3]={0,1,4};
 kernel_fixture(2,3,a,seq);
 if(fwrite(a,1,sizeof(a),stdout)!=sizeof(a))return 1;
 return fflush(stdout)!=0;
}
'''
class Tests(unittest.TestCase):
    def test_json_duplicate(self):
        with self.assertRaises(BuildError): parse_json('{"a":1,"a":2}')
    def test_json_nan(self):
        with self.assertRaises(BuildError): parse_json('{"a":NaN}')
    def test_static_removal(self): self.assertEqual(external_function('static\nvoid k(){}'),'void k(){}')
    def test_nonstatic_unchanged(self): self.assertEqual(external_function('void k(){}'),'void k(){}')
    def test_comments(self):
        s='/* for ( } */\n"{}" // for (\nvoid k(){}'; m=mask_noncode(s)
        self.assertEqual(len(s),len(m)); self.assertEqual(s.count('\n'),m.count('\n')); self.assertNotIn('for',m)
    def test_prototype_ignored(self): self.assertEqual(function_span('void k(); void k(){}','k'),(10,20))
    def test_duplicate_function(self):
        with self.assertRaises(BuildError): function_span('void k(){} void k(){}','k')
    def test_unclosed_comment(self):
        with self.assertRaises(BuildError): mask_noncode('/* bad')
    def test_body_preserved(self):
        k,d=isolate(FIXTURE,'kernel_fixture','typedef char base;\n')
        self.assertEqual(body(FIXTURE,'kernel_fixture'),body(k,'kernel_fixture'))
        self.assertNotIn('static void kernel_fixture',k); self.assertNotIn('sqrt((double)seq',d)
    def test_typedef(self): self.assertEqual(local_typedefs(FIXTURE,FIXTURE),'typedef char base;\n')
    def test_typedef_missing(self):
        with self.assertRaises(BuildError): local_typedefs('typedef char base;','')
    def test_ir_preserve_declarations(self):
        s='source_filename = "tmp.c"\ndeclare double @sqrt(double)\nattributes #0 = { noinline "target-cpu"="x86-64" }\n!0 = !{i32 1}\n'
        x=sanitize_ir(s); self.assertIn('declare double @sqrt',x); self.assertIn('noinline',x); self.assertIn('!0 =',x)
        self.assertNotIn('target-cpu',x)
    def test_ir_reject_cpu(self):
        with self.assertRaises(BuildError): sanitize_ir('; haswell')
    def test_raw_print_single_statement(self):
        s='static void print_array(int n,double *a){for(int i=0;i<n;i++) fprintf(POLYBENCH_DUMP_TARGET,DATA_PRINTF_MODIFIER,a[i]);}\nvoid kernel_k(){}'
        raw,n=raw_print_source(s); self.assertEqual(n,1); self.assertIn('do {',raw); self.assertEqual(body(s,'kernel_k'),body(raw,'kernel_k'))
    def test_split_args(self): self.assertEqual(split_args('a,f(b,c),d[i,j]'),['a','f(b,c)','d[i,j]'])
    def test_nonempty(self): self.assertFalse(exact(b'',b''))
    def test_corrupted_output(self): self.assertFalse(exact(b'abc',b'abd'))
    def test_truncated_output(self): self.assertFalse(exact(b'abc',b'ab'))
    def test_signed_zero_different(self):
        import struct
        self.assertFalse(exact(struct.pack('d',0.),struct.pack('d',-0.)))
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';write(p,'a')
            with self.assertRaises(FileExistsError): write(p,'b')
    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(BuildError): safe_file(Path(t),'../bad')
    def test_failed_command_is_not_pass(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(BuildError):run([sys.executable,'-c','raise SystemExit(3)'],Path(t)/'r')
    def test_timeout_is_not_pass(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(BuildError):run([sys.executable,'-c','import time; time.sleep(3)'],Path(t)/'r',timeout=.05)
    def test_preprocessed_unbraced_raw_output_roundtrip(self):
        clang,_=pick_clang(strict=False)
        source = r'''
#include <stdio.h>
#include <stdlib.h>
#define DATA_TYPE double
#define POLYBENCH_DUMP_TARGET stderr
#define DATA_PRINTF_MODIFIER "%lf"
#define N 2
#define M 3
static void kernel_fixture(int n,int m,DATA_TYPE a[n][m]) {
 int i,j;
 for(i=0;i<n;i++)
  for(j=0;j<m;j++)
   if(j>0) a[i][j]+=1.25;
}
static void print_array(int n,int m,DATA_TYPE a[n][m]) {
 for(int i=0;i<n;i++)
  for(int j=0;j<m;j++)
   fprintf(POLYBENCH_DUMP_TARGET,DATA_PRINTF_MODIFIER,a[i][j]);
}
int main(void){DATA_TYPE a[N][M]={{-0.,1,2},{3,4,5}};kernel_fixture(N,M,a);print_array(N,M,a);return 0;}
'''
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); raw,n=raw_print_source(source);self.assertEqual(n,1)
            write(root/'raw.c',raw)
            pp=run([clang,*CFLAGS,'-E','-P',root/'raw.c'],root/'pp').decode()
            r=materialize(pp,'kernel_fixture','',root/'case',clang,expected_loops=2)
            self.assertTrue(r['passed']); self.assertEqual(r['output_bytes'],48)
    def test_vla_math_ir_dependencies_roundtrip(self):
        clang,_=pick_clang(strict=False)
        s = r'''#include <stdio.h>
#include <math.h>
static void kernel_fixture(int n,float *a){float temp[n];for(int i=0;i<n;i++)temp[i]=expf(a[i]);for(int i=0;i<n;i++)a[i]=temp[i];}
int main(void){float a[3]={0.,1.,-1.};kernel_fixture(3,a);return fwrite(a,1,sizeof(a),stdout)!=sizeof(a);}
'''
        with tempfile.TemporaryDirectory() as t:
            r=materialize(s,'kernel_fixture','',Path(t)/'case',clang,expected_loops=2)
            self.assertTrue(r['passed'])
    def test_roundtrip_with_real_clang(self):
        clang,_=pick_clang(strict=False)
        with tempfile.TemporaryDirectory() as t:
            r=materialize(FIXTURE,'kernel_fixture','typedef char base;\n',Path(t)/'case',clang,expected_loops=2)
            self.assertTrue(r['passed']);self.assertEqual(r['correctness_executions'],6)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--clang');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    try:
        require(sys.byteorder=='little','little-endian x86_64 Linux環境を使用してください')
        clang,version=pick_clang(a.clang); return execute(a.repo,clang,version)
    except Exception as exc:
        print('CODEGEN_ROUNDTRIP_BLOCKED:',type(exc).__name__+': '+str(exc),file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
