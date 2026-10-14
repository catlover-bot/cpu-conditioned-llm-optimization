#!/usr/bin/env python3
"""Append-only Zen2 P0 -> P1 -> P2 campaign, using the fixed codegen evaluator.
Only condition-specific prompts and sequence control are new. Never resubmit P0,
never pass model answers or measured timings to a later condition, never weaken
isolation. No aggregate deadline; per-request limits and safety stops remain.
"""
from __future__ import annotations
import argparse
import ast
import copy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid

P0 = Path('/srv/research/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent')
FULL = Path('/srv/research/cpucond-batch-en-20260912T074659-7093')
SUPPLEMENT = Path(str(FULL)+'-context6-v1')
ROOT = Path('/srv/research/cpucond-p012-zen2-v1')
AUDIT = Path('/srv/research/cpucond-token-audit-20260912T102556')
MODEL = 'qwen2.5-coder:32b-instruct-q4_K_M'
MODEL_SHA = 'b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41'
P0_SHA = '6abe9c69297a494c0f5df736da1c76d2d789f326567359dc32e3c7c293be848d'
FULL_SHA = '1606a944f79e5e445f3511414f39d8eeee60617b575b596b932374d65f56eac6'
SUPPLEMENT_SHA = '97de40c0a9d4346d576525e30f1965ee09faeae2a58f10ef3bd38bc57c32db77'
REV = 'polybench-direct-codegen-zen2-p12-v1'
CAPS = {'C':4096,'IR':16384}
FORMS = ('C','IR')
CONDITIONS = ('P1','P2')
P0_LINE = 'No CPU-specific model name or performance information is supplied. This is condition P0.'
BEGIN = '----- BEGIN ORIGINAL CODE -----\n'
END = '----- END ORIGINAL CODE -----'
BASE_HASHES = {
 'goal0069_batch_codegen.py':'c0f16b48924a81320aee74f16b6b136503667d648a0dc2ee61e2c807c53fc47c',
 'runtime_support.py':'65e8fa3acdbb8242a9c1300757439f56ca699a350c49cf6c9b9b85d93f6c0eed',
 'streaming_support.py':'6fb3e1548e6deaf817d1dfd07348fb359112b4917751c09787de955b20bc1fd5',
 'roundtrip_support.py':'caae960ddf1c919eb24c14ab55b85e9b35d351b966c1acf485816c31a88ff886',
 'model_support.py': '28e86abfaac3492690d11f3353983e94e13d3a83a1e08ca55bb2836d52904e23',
 'stress_support.py': '809819e965bb7ec80487d4fb65c5313e1b00e4378ced059fd36d9e1bef22ee8e',
}
C74 = ('goal0074_finish_all.py','until_complete_pipeline.py','pipeline-change.diff','SHA256SUMS')
LIMIT = 64*1024*1024
class Refuse(RuntimeError): pass

def need(ok, msg):
    if not ok: raise Refuse(msg)
def utc(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),'通常ファイルではありません: '+str(p))
    with p.open('rb') as f: raw=f.read(LIMIT+1)
    need(len(raw)<=LIMIT,'ファイルが大きすぎます: '+str(p));return raw
def decode(raw):
    def pairs(xs):
        d={}
        for k,v in xs:need(k not in d,'JSONキー重複');d[k]=v
        return d
    def fail(s):raise Refuse('非有限JSON: '+s)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=fail)
def load(p):return decode(read(p))
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def write(p, raw):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def jw(p,x):write(p,enc(x))
def atomic(p,x):
    p=Path(p);need(not p.is_symlink(),'出力先がリンクです')
    q=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex);write(q,enc(x));os.replace(q,p)
def text_atomic(p,text):
    p=Path(p);need(not p.is_symlink(),'出力先がリンクです')
    q=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex);write(q,text.encode());os.replace(q,p)
def safe(root,rel):
    need(isinstance(rel,str) and rel and '\\' not in rel,'パスが不正')
    parts=PurePosixPath(rel);need(not parts.is_absolute() and '..' not in parts.parts,'範囲外パス')
    root=Path(root).resolve();p=root.joinpath(*parts.parts)
    need(p.resolve().is_relative_to(root) and p!=root,'範囲外パス')
    for a in [p,*p.parents]:
        if a==root:break
        need(not a.is_symlink(),'リンクを拒否')
    return p

def verify_tree(root, name='SHA256SUMS'):
    table={}
    for line in read(root/name).decode().splitlines():
        h,sep,rel=line.partition('  ')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and rel not in table,'ハッシュ一覧が不正')
        need(digest(read(safe(root,rel)))==h,'ハッシュ不一致: '+rel);table[rel]=h
    need(table,'空のハッシュ一覧');return table

def seal(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),'リンクを拒否')
        if p.is_file() and p.name!='SHA256SUMS':rows.append(digest(read(p))+'  '+p.relative_to(root).as_posix()+'\n')
    write(root/'SHA256SUMS',''.join(rows).encode())

def command(args, **kw):return subprocess.run(args,check=True,timeout=30,**kw)
def state(unit):
    need(re.fullmatch(r'cpucond[0-9]+-[A-Za-z0-9-]+\.service',unit),'サービス名不正')
    p=subprocess.run(['systemctl','show',unit,'-p','ActiveState','--value'],capture_output=True,text=True,timeout=15,env={**os.environ,'LC_ALL':'C'})
    if p.returncode:
        need('not found' in p.stderr.lower() or 'could not be found' in p.stderr.lower(),'サービス状態取得失敗')
        return 'inactive'
    value=p.stdout.strip();need(value in ('active','activating','reloading','deactivating','inactive','failed'),'不明なサービス状態');return value

def live(value):return value in ('active','activating','reloading','deactivating')
def host():
    need(os.geteuid()==0,'サーバー管理者として起動してください')
    need(Path('/proc/sys/kernel/hostname').read_text().strip()=='cpucond-zen2-01','対象ホストが違います')
    need(re.search(r'AMD EPYC 7402\b',Path('/proc/cpuinfo').read_text()),'対象CPUが違います')

def import_path(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

def cpu_list(text):
    out=set()
    for part in text.strip().split(','):
        need(re.fullmatch(r'\d+(?:-\d+)?',part),'CPU一覧の形式不正')
        a,*rest=map(int,part.split('-'));b=rest[0] if rest else a
        need(0<=a<=b<65536,'CPU番号の範囲不正');out.update(range(a,b+1))
    return sorted(out)

def cache_bytes(text):
    m=re.fullmatch(r'(\d+)([KMG]?)',text.strip());need(m,'キャッシュ容量の形式不正')
    n=int(m[1])*(1024**{'':0,'K':1,'M':2,'G':3}[m[2]])
    need(n>0,'キャッシュ容量0');return n

def capture_hardware(syscpu=Path('/sys/devices/system/cpu'),sysnode=Path('/sys/devices/system/node'),proc=Path('/proc')):
    """Read only static cache/topology and separate execution-state evidence.
    Never measures latency/bandwidth/counters, reads model outputs, or estimates
    a per-core L3 capacity from a machine-wide total.
    """
    raw={}
    def take(p):
        value=p.read_text().strip();raw[str(p)]=value;return value
    present=cpu_list(take(syscpu/'present'));online=cpu_list(take(syscpu/'online'))
    need(set(online)<=set(present) and 2 in online,'CPU構成不正')
    info=take(proc/'cpuinfo');blocks={}
    for block in info.split('\n\n'):
        fields={k.strip():v.strip() for line in block.splitlines() if ':' in line for k,v in [line.split(':',1)]}
        if fields.get('processor','').isdigit():blocks[int(fields['processor'])]=fields
    need(2 in blocks and re.search(r'AMD EPYC 7402\b',blocks[2].get('model name','')),'CPU2の製品名不一致')
    topology=[]
    for cpu in online:
        base=syscpu/f'cpu{cpu}'
        core=int(take(base/'topology/core_id'));package=int(take(base/'topology/physical_package_id'))
        need(core>=0 and package>=0,'CPUのトポロジーIDが不明')
        nodes=sorted(int(p.name[4:]) for p in base.glob('node[0-9]*') if re.fullmatch(r'node\d+',p.name))
        need(len(nodes)==1,'CPUのNUMAノードが一意ではありません')
        topology.append({'cpu':cpu,'core':core,'socket':package,'node':nodes[0]})
    selected=next(x for x in topology if x['cpu']==2)
    need(selected['socket']==0 and selected['node']==0,'評価CPUの場所が以前と違います')
    groups={s:{x['core'] for x in topology if x['socket']==s} for s in {x['socket'] for x in topology}}
    need(len(groups)==2 and all(len(g)==24 for g in groups.values()),'期待した2ソケット×24コアではありません')
    siblings=cpu_list(take(syscpu/'cpu2/topology/thread_siblings_list'))
    # Some kernels omit offline siblings. Record what was observed, not invent 2.
    flags=set(blocks[2].get('flags','').split())
    wanted=('sse','sse2','sse3','pni','ssse3','sse4_1','sse4_2','avx','avx2','fma','f16c','bmi1','bmi2')
    isa=[f for f in wanted if f in flags]
    caches=[]
    for p in sorted((syscpu/'cpu2/cache').glob('index[0-9]*')):
        typ=take(p/'type');level=int(take(p/'level'));size=cache_bytes(take(p/'size'))
        shared=cpu_list(take(p/'shared_cpu_list'))
        need(2 in shared,'CPU2がキャッシュ共有一覧にありません')
        cores={(x['socket'],x['core']) for x in topology if x['cpu'] in shared}
        c={'level':level,'type':typ,'size_bytes':size,'line_bytes':int(take(p/'coherency_line_size')),
           'ways':int(take(p/'ways_of_associativity')),'sets':int(take(p/'number_of_sets')),
           'shared_logical_cpu_ids_reported':shared,'online_physical_cores_in_domain':len(cores)}
        if (p/'id').exists():c['cache_id']=int(take(p/'id'))
        caches.append(c)
    need({(x['level'],x['type']) for x in caches}>={(1,'Data'),(1,'Instruction'),(2,'Unified'),(3,'Unified')},'キャッシュ情報が不足')
    nodes=cpu_list(take(sysnode/'online'))
    runtime={'smt_active':take(syscpu/'smt/active'),'boost':take(syscpu/'cpufreq/boost'),
       'cpu2_governor':take(syscpu/'cpu2/cpufreq/scaling_governor')}
    need(runtime=={'smt_active':'0','boost':'0','cpu2_governor':'performance'},'評価時CPU設定が変わっています')
    key={'product_name':'AMD EPYC 7402','microarchitecture':'Zen 2',
         'model_name_observed':blocks[2]['model name'],
         'family':blocks[2].get('cpu family'),'model':blocks[2].get('model'),'stepping':blocks[2].get('stepping'),
         'installed_logical_processor_count':len(present),'online_physical_core_count':sum(len(v) for v in groups.values()),
         'socket_count':len(groups),'physical_cores_per_socket':{str(s):len(v) for s,v in sorted(groups.items())},
         'numa_node_count':len(nodes),'cpu2_smt_siblings_reported':siblings,'cache_domains_for_cpu2':caches,
         'relevant_isa_flags_reported':isa,'evaluation_cpu':2,'evaluation_node':0}
    freeze={'machine_id':take(Path('/etc/machine-id')) if proc==Path('/proc') else 'test-machine',
            'boot_id':take(proc/'sys/kernel/random/boot_id') if (proc/'sys/kernel/random/boot_id').exists() else None}
    return {'schema':'cpucond-static-host-profile-v1','recorded_utc':utc(),'static_profile':key,
            'execution_state_not_added_to_P2':runtime,'host_identity':freeze,'raw_readonly_evidence':raw,
            'microarchitecture_source':'AMD EPYC 7002 product family / fixed experiment target Zen 2',
            'no_measured_kernel_performance_read':True,'no_bandwidth_or_latency_inferred':True}

def info_block(profile,condition):
    need(condition in CONDITIONS,'P1/P2以外です')
    p=profile['static_profile'];need(p['product_name']=='AMD EPYC 7402' and p['microarchitecture']=='Zen 2','対象CPU不一致')
    lines=[f'Target CPU information (condition {condition}):',
           '- CPU model: AMD EPYC 7402.', '- Microarchitecture: Zen 2.']
    if condition=='P2':
        lines += [f'- Physical sockets in the machine: {p["socket_count"]}.',
          '- Physical cores per socket: '+', '.join(f'socket {s}: {n}' for s,n in p['physical_cores_per_socket'].items())+'.',
          f'- Logical processor slots reported present: {p["installed_logical_processor_count"]}.',
          f'- NUMA nodes reported online: {p["numa_node_count"]}.',
          '- Cache hierarchy for the evaluation core (each size is one cache sharing domain, not a sum across the machine):']
        for c in p['cache_domains_for_cpu2']:
            lines.append(f'  - L{c["level"]} {c["type"]}: {c["size_bytes"]//1024} KiB; line {c["line_bytes"]} bytes; '
                f'{c["ways"]}-way; {c["sets"]} sets; shared by {c["online_physical_cores_in_domain"]} online physical core(s).')
        lines += ['- Relevant ISA flags reported by the operating system: '+', '.join(p['relevant_isa_flags_reported'])+'.',
             '- ISA availability does not override the common correctness contract, including its FMA prohibition.']
    text='\n'.join(lines)
    need(text.isascii(),'CPU情報が英語/ASCIIではありません');return text

def condition_request(old,source,condition,profile,tokenizer):
    need(old.get('model')==MODEL and old.get('raw') is True,'元要求形式不一致')
    prompt=old['prompt'];need(prompt.count(P0_LINE)==1 and prompt.count(BEGIN)==1 and prompt.count(END)==1,'固定テンプレート不一致')
    code=prompt.split(BEGIN)[1].split(END)[0]
    need(code==source.rstrip()+'\n','元コードと要求が一致しません')
    block=info_block(profile,condition)
    new=copy.deepcopy(old);new['prompt']=prompt.replace(P0_LINE,block,1)
    form='IR' if 'a complete LLVM 18 textual IR module' in prompt else 'C'
    need(form=='IR' or 'a complete C translation unit' in prompt,'出力形式不明')
    new['stream']=True;new['options']['num_predict']=CAPS[form]
    need(new['options']['num_ctx']==32768,'文脈長変更')
    # Normalize only the already adopted resource73 changes to compare params.
    normalized=copy.deepcopy(old);normalized['stream']=True;normalized['options']['num_predict']=CAPS[form]
    compare=copy.deepcopy(new);compare['prompt']=prompt
    need(compare==normalized,'CPU説明以外の条件が変わりました')
    ids=tokenizer.encode(new['prompt'],add_special_tokens=False).ids
    need(tokenizer.decode(ids,skip_special_tokens=False)==new['prompt'],'トークナイザー往復不一致')
    count=len(ids);nsource=len(tokenizer.encode(source.rstrip(),add_special_tokens=False).ids)
    need(count+CAPS[form]+32<=32768,'追加CPU情報で文脈長超過。除外せず停止')
    need(nsource+64<=CAPS[form],'元コードの出力枠不足。除外せず停止')
    return new,{'input_tokens':count,'source_tokens':nsource,'output_cap':CAPS[form],
                'context_slack':32768-count-CAPS[form]-32}

def verify_sources():
    need(digest(read(P0/'work/plan.json'))==P0_SHA,'新版P0計画が違います')
    need(digest(read(FULL/'work/plan.json'))==FULL_SHA,'元180件計画が違います')
    need(digest(read(SUPPLEMENT/'work/plan.json'))==SUPPLEMENT_SHA,'補完計画が違います')
    new=load(P0/'work/plan.json');full=load(FULL/'work/plan.json')
    need(new['requests']==166 and len(new['tasks'])==166 and full['requests']==180 and len(full['tasks'])==180,'対象件数不一致')
    need(full['conditions']==['P0'] and full['prompt_language']=='en','元の実験条件不一致')
    ids={x['id'] for x in full['tasks']};need(len(ids)==180,'要求ID重複')
    need({x['id'] for x in new['tasks']}<=ids,'新版P0に未知の要求')
    hs=verify_tree(FULL/'work');ns=verify_tree(P0/'work')
    for name,expected in BASE_HASHES.items():
        if expected:need(ns.get(name)==expected,'共通実行器が異なります: '+name)
    return full,new,hs,ns

def verify_installed(root):
    table=verify_tree(root/'control')
    campaign=load(root/'control/campaign.json')
    need(campaign['p0_job']==str(P0) and campaign['condition_order']==['P0','P1','P2'],'別の連鎖設定です')
    for condition in CONDITIONS:
        work=root/condition/'work';hashes=verify_tree(work)
        need(hashes['plan.json']==campaign['plans_sha256'][condition],'条件計画が変化')
        p=load(work/'plan.json');need(p['conditions']==[condition] and p['requests']==180,'条件/件数不一致')
        for n,h in campaign['base_implementation_hashes'].items():need(hashes.get(n)==h,'条件間の実行器相違')
    return campaign

def prepare(root,kit,tokenizer,profile):
    if root.exists():
        need(not root.is_symlink(),'既存連鎖ディレクトリがリンクです');verify_installed(root)
        need(digest(read(root/'control/goal0075_p012_chain.py'))==digest(read(kit/'goal0075_p012_chain.py')),'以前と違う連鎖器です')
        print('P012_CHAIN_REUSED',flush=True);return
    full,p0,oldhash,basehash=verify_sources()
    keys={(x['task'],x['size']) for x in full['instances_list']}
    need(len(keys)==90 and len({t for t,s in keys})==30,'30x3条件不一致')
    equal_ids={t['id'] for t in p0['tasks']}
    stage=root.with_name(root.name+'.preparing-'+uuid.uuid4().hex[:8]);stage.mkdir()
    try:
        control=stage/'control';control.mkdir()
        for name in ('goal0075_p012_chain.py',):write(control/name,read(kit/name))
        for name in C74:write(control/'finish74'/name,read(kit/'finish74'/name))
        jw(control/'hardware-profile.json',profile)
        write(control/'P1-hardware-block.txt',(info_block(profile,'P1')+'\n').encode())
        write(control/'P2-hardware-block.txt',(info_block(profile,'P2')+'\n').encode())
        baseline_impl={name:basehash[name] for name in BASE_HASHES}
        plans={};allrows=[]
        shared={'utilities/polybench.c','utilities/polybench.h'}
        for instance in full['instances_list']:
            shared.update((instance['driver'],instance['oracle']))
            shared.update(x['path'] for x in instance['sources'].values())
        bykey={(i['task'],i['size']):i for i in full['instances_list']}
        for condition in CONDITIONS:
            work=stage/condition/'work';work.mkdir(parents=True)
            for rel in sorted(shared):
                raw=read(safe(FULL/'work',rel));need(digest(raw)==oldhash[rel],'元入力のハッシュ不一致');write(work/rel,raw)
            for name,h in baseline_impl.items():
                raw=read(P0/'work'/name);need(digest(raw)==h,'実行器のコピー時変更');write(work/name,raw)
            items=[]
            for t in full['tasks']:
                source=read(safe(FULL/'work',t['source']))
                need(digest(source)==bykey[(t['task'],t['size'])]['sources'][t['form']]['sha256'],'元コード不一致')
                raw=read(safe(FULL/'work',t['request']));need(digest(raw)==t['request_sha256'],'元要求不一致')
                new,budget=condition_request(decode(raw),source.decode(),condition,profile,tokenizer)
                tid=t['id'].replace('__P0__','__'+condition+'__')
                need(tid!=t['id'] and re.fullmatch(r'[A-Za-z0-9_-]+',tid),'条件IDの変換失敗')
                newraw=enc(new);rel='requests/'+tid+'.json';write(work/rel,newraw)
                item=copy.deepcopy(t);item.update(id=tid,condition=condition,request=rel,request_sha256=digest(newraw),
                    original_p0_id=t['id'],original_p0_request_sha256=t['request_sha256'],
                    context_budget_ok=True,reference_tokenizer_input_tokens=budget['input_tokens'],
                    input_byte_upper=len(new['prompt'].encode())+32,source_output_tokens=budget['source_tokens'],
                    resource_policy=REV,request_timeout_seconds=1800 if t['form']=='C' else 7200)
                items.append(item);allrows.append({'condition':condition,'id':tid,'original_p0_id':t['id'],
                  'p0_equal_resource_policy':t['id'] in equal_ids,**budget})
            plan=copy.deepcopy(full)
            plan.update(revision=REV,prompt_revision='direct-codegen-en-v2-hardware-v1',conditions=[condition],
                requests=180,tasks=items,output_caps=CAPS,additional_calls_for_P1_P2=True,scope=condition+' / Zen 2 / one model / one trial / provisional',
                context_policy='official tokenizer + unchanged-source output + fixed reserves',
                cpu_prompt_condition={'condition':condition,'target_cpu':'AMD EPYC 7402','target_microarchitecture':'Zen 2',
                    'static_profile_sha256':digest(enc(profile['static_profile'])),'hardware_block':info_block(profile,condition),
                    'measured_performance_in_prompt':False,'prior_answers_in_prompt':False},
                resource_policy={'based_on':'goal0073','caps':CAPS,'request_seconds':{'C':1800,'IR':7200},
                    'stream_idle_seconds':1800,'session_limit_seconds':None,'generation_window_seconds':None},
                comparison={'source_p0_full_sha256':FULL_SHA,'source_p0_amended_sha256':P0_SHA,
                    'equal_resource_p0_ids':sorted(equal_ids),'legacy_p0_ids_not_same_budget':sorted({t['id'] for t in full['tasks']}-equal_ids),
                    'all_30_multiinput_validation_complete':False,'fixed_order_time_confound_not_eliminated':True})
            # Remove the old time-limited scheduling recipe from condition metadata.
            for name in ('resource_amendment','execution_budget'):plan.pop(name,None)
            jw(work/'plan.json',plan);plans[condition]=digest(read(work/'plan.json'));seal(work)
        with (control/'context-and-pairing-audit.csv').open('x',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
        campaign={'revision':'cpucond-p012-sequence-zen2-v1','prepared_utc':utc(),
            'condition_order':['P0','P1','P2'],'p0_job':str(P0),'full_p0_job':str(FULL),
            'supplement_p0_job':str(SUPPLEMENT),'additional_requests':360,'p1_requests':180,'p2_requests':180,
            'source_p0_current_sha256':P0_SHA,'source_p0_full_sha256':FULL_SHA,
            'plans_sha256':plans,'base_implementation_hashes':baseline_impl,
            'model':MODEL,'model_manifest_sha256':MODEL_SHA,'prompt_language':'en','samples_per_condition':1,
            'profile_sha256':digest(enc(profile)),
            'execution_host':'cpucond-zen2-01','automatic_other_host_or_provider':False,
            'global_time_limit_seconds':None,'retry_failed_candidate':False,'background_budget_updates':False,
            'p0_original_total':180,'p0_amended166':166,'p0_old_budget14':14,
            'same_budget_comparison_ids':sorted(equal_ids),
            'transition_requires_full_terminal_results_not_all_pass':True,
            'stop_on_safety_infrastructure_or_consecutive_transport_error':True,
            'sequential_order_confound_recorded':True,
            'gpu_or_haswell_measurements_in_this_campaign':False}
        jw(control/'campaign.json',campaign);seal(control);stage.rename(root)
    except Exception:
        shutil.rmtree(stage,ignore_errors=True);raise
    print('P012_CHAIN_PREPARED',flush=True)
    print('P0は既存結果を継続。P1=180件、P2=180件。英語のCPU情報ブロックだけを変更。',flush=True)
    print('全360要求で文脈長・元コードの出力枠を確認。P0要求の再送=0。',flush=True)
    print('=== P2へ渡す実機の静的情報 ===\n'+info_block(profile,'P2'),flush=True)

def setstatus(root,phase,**kw):atomic(root/'status.json',{'phase':phase,'utc':utc(),'campaign_root':str(root),'total_wall_time_limit_seconds':None,**kw})

def finish74(root):
    module=import_path('cpucond75_finish74',root/'control/finish74/goal0074_finish_all.py')
    module.verify_kit(root/'control/finish74');return module

def completed(summary,expected):
    return (summary.get('completion')=='DATASET_BATCH_COMPLETE' and type(summary.get('planned_requests')) is int
      and summary['planned_requests']==expected and summary.get('generation_terminal')==expected
      and summary.get('validation_terminal')==expected and summary.get('measurement_pending')==0
      and not summary.get('current_session',{}).get('errors'))

def summary_exists_complete(job,n):
    return (job/'results/summary.json').is_file() and completed(load(job/'results/summary.json'),n)

def wait_service(root,condition,job,unit,query=state,pause=time.sleep):
    last=None
    while live(query(unit)):
        phase='WAITING_FOR_P0' if condition=='P0' else 'RUNNING_'+condition
        setstatus(root,phase,active_condition=condition,active_job=str(job),active_unit=unit,automatic_next_condition=True)
        if phase!=last:print('P012_'+phase,flush=True);last=phase
        pause(60)
    need(summary_exists_complete(job,166 if condition=='P0' else 180),condition+'が完了条件を満たしていません。次条件へ進みません')
    setstatus(root,condition+'_COMPLETE',active_condition=condition,active_job=str(job))

def base_module(work):
    sys.dont_write_bytecode=True
    for n,h in BASE_HASHES.items():
        if h:need(digest(read(work/n))==h,'実行器ハッシュ不一致: '+n)
    sys.path.insert(0,str(work))
    return import_path('cpucond75_fixed_base',work/'goal0069_batch_codegen.py')

def p0_receipt(root):
    """Cross-check 180 unique IDs, including retained 14 old-budget attempts.
    This is provenance/completion bookkeeping, never prompt input.
    """
    full=load(FULL/'work/plan.json');current=load(P0/'work/plan.json');curids={t['id'] for t in current['tasks']}
    b=base_module(P0/'work');counts=b.results_summary(current,P0/'results')
    need(counts['generation_terminal']==166 and counts['validation_terminal']==166 and counts['measurement_pending']==0,'P0個別記録と要約が不一致')
    rows=[]
    for t in full['tasks']:
        tid=t['id']
        roots=[P0] if tid in curids else [FULL,SUPPLEMENT]
        found=[]
        for source in roots:
            g=source/'results/generation'/tid/'result.json'
            if g.exists() and load(g).get('status')!='input_budget_excluded':found.append(source)
        need(len(found)==1,'P0の実送信結果が一意ではありません: '+tid)
        source=found[0];v=source/'results/validation'/tid/'result.json';need(v.is_file(),'P0の検証記録が不足: '+tid)
        eligible=load(v).get('measurement_eligible_provisional',False)
        m=source/'results/measurement'/tid/'result.json';need(not eligible or m.is_file(),'P0の対象計測が未完了: '+tid)
        rows.append({'id':tid,'job':str(source),'generation_sha256':digest(read(source/'results/generation'/tid/'result.json')),
          'validation_sha256':digest(read(v)),'measurement_sha256':digest(read(m)) if m.exists() else None,
          'same_budget_as_p1_p2':tid in curids})
    need(len(rows)==180,'P0個数不一致')
    path=root/'p0-completion-receipt.json'
    value={'p0_unique_requests':180,'new_budget':166,'legacy_budget':14,'rows':rows}
    if path.exists():need(load(path)==value,'以前のP0結果が変化')
    else:jw(path,value)
    return value

def stage_command(root,condition,unit,parent_unit):
    job=root/condition
    return ['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
      '--property=RuntimeMaxSec=infinity','--property=MemoryMax=96G','--property=TasksMax=256',
      '--property=TimeoutStopSec=20','--property=KillMode=control-group','--property=PartOf='+parent_unit,
      '--property=StandardOutput=append:'+str(job/'run.log'),'--property=StandardError=append:'+str(job/'run.log'),
      '--setenv=CPUCOND_BATCH_UNIT='+unit,'--setenv=PYTHONDONTWRITEBYTECODE=1',
      '--working-directory='+str(job/'work'),'/usr/bin/python3','-B','-u',str(root/'control/goal0075_p012_chain.py'),
      '--stage-worker','--condition',condition,'--root',str(root)]

def start_stage(root,condition,parent_unit):
    job=root/condition;marker=job/'active-unit.txt'
    if marker.exists():
        unit=read(marker).decode().strip()
        if live(state(unit)):return unit
    need(not summary_exists_complete(job,180),'完了済みの条件は起動しません')
    previous=job/'results/summary.json'
    if previous.exists():
        x=load(previous);need(x.get('completion')!='DATASET_BATCH_BLOCKED' and not x.get('current_session',{}).get('errors'),
            condition+'に安全/環境エラーがあります。自動的には再開しません')
    unit='cpucond69-sequence75-'+condition+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.service'
    text_atomic(marker,unit+'\n');command(stage_command(root,condition,unit,parent_unit),stdin=subprocess.DEVNULL)
    print('P012_STAGE_STARTED '+condition+' unit='+unit,flush=True);return unit

def orchestrate(root):
    host();campaign=verify_installed(root)
    unit=os.environ.get('CPUCOND_CHAIN_UNIT','')
    need(re.fullmatch(r'cpucond75-p012-[A-Za-z0-9-]+\.service',unit),'連鎖サービス名不正')
    need(unit in Path('/proc/self/cgroup').read_text(),'連鎖サービスの所属不一致')
    with open('/var/lock/cpucond-p01275-worker.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        f=finish74(root)
        if not summary_exists_complete(P0,166):
            # launch() detects a previously installed/running goal0074 controller.
            # It never interrupts the current finite-duration P0 session.
            f.launch(P0)
            if not summary_exists_complete(P0,166):
                p0unit=read(P0/f.CONTROL/'active-unit.txt').decode().strip()
                wait_service(root,'P0',P0,p0unit)
        p0_receipt(root)
        print('P012_P0_COMPLETE unique=180 (resource-v2=166, legacy=14)',flush=True)
        for condition in CONDITIONS:
            if not summary_exists_complete(root/condition,180):
                child=start_stage(root,condition,unit);wait_service(root,condition,root/condition,child)
            # Recount from individual result files, not merely success exit codes.
            b=base_module(root/condition/'work');plan=load(root/condition/'work/plan.json')
            x=b.results_summary(plan,root/condition/'results')
            need(x['generation_terminal']==180 and x['validation_terminal']==180 and x['measurement_pending']==0,
                 condition+'個別記録の処理未完了')
        setstatus(root,'P012_ALL_COMPLETE',condition_order=['P0','P1','P2'],p0_unique_requests=180,p1_requests=180,p2_requests=180,
                  all_candidates_correct=False,formal_equivalence_proven=False,
                  all_30_multiinput_validator_complete=False,cpu_effect_estimated=False)
        print('P012_ALL_COMPLETE\n全条件の処理終了。全生成コードの正しさ合格を意味しません。契約は変更しません。',flush=True)

def stage_worker(root,condition):
    host();need(condition in CONDITIONS,'条件名不正');campaign=verify_installed(root)
    job=root/condition;work=job/'work';plan=load(work/'plan.json')
    unit=os.environ.get('CPUCOND_BATCH_UNIT','')
    need(re.fullmatch(r'cpucond69-sequence75-'+condition+r'-[A-Za-z0-9-]+\.service',unit),'子サービス名不正')
    need(unit in Path('/proc/self/cgroup').read_text(),'子サービス所属不一致')
    need(command(['systemctl','show',unit,'-p','RuntimeMaxUSec','--value'],capture_output=True,text=True).stdout.strip()=='infinity','時間上限が残っています')
    # A stage never runs simply because it has been invoked directly.
    need(summary_exists_complete(P0,166) and (root/'p0-completion-receipt.json').is_file(),'P0未完了')
    if condition=='P2':need(summary_exists_complete(root/'P1',180),'P1未完了')
    expected_profile=load(root/'control/hardware-profile.json');actual=capture_hardware()
    for key in ('static_profile','execution_state_not_added_to_P2','host_identity'):
        need(actual[key]==expected_profile[key],'実機/起動/静的情報が準備時と異なります: '+key)
    freeze=load(Path('/var/lib/cpucond-infer/goal0067/repo/model-freeze.json'))
    need(freeze.get('model')==MODEL and freeze.get('manifest_sha256')==MODEL_SHA,'固定32Bモデルが変化')
    b=base_module(work)
    b.REV=REV;b.PROMPT_REVISION='direct-codegen-en-v2-hardware-v1'
    original_summary=b.results_summary
    def condition_summary(p,r):
        result=original_summary(p,r)
        result.update(condition=condition,cpu_prompt_condition=p['cpu_prompt_condition'],
                      comparison_budget_note='P0 legacy14 separate; matched resource166; one trial per condition')
        return result
    b.results_summary=condition_summary
    code=read(root/'control/finish74/until_complete_pipeline.py').decode()
    tree=ast.parse(code);need(len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef),'制御関数形式不正')
    exec(compile(code,str(root/'control/finish74/until_complete_pipeline.py'),'exec'),b.__dict__)
    (job/'results').mkdir(exist_ok=True)
    jw(job/'results'/('condition-start-'+uuid.uuid4().hex[:8]+'.json'),{'utc':utc(),'condition':condition,
       'prompt_language':'en','plan_sha256':digest(read(work/'plan.json')),'model_expected':MODEL_SHA,
       'host_profile_sha256':campaign['profile_sha256'],'next_stage_requires_terminal_records':True})
    print('P012_STAGE_RUNNING '+condition+' / 180 requests / no total time limit',flush=True)
    rc=b.run_pipeline_until_complete(work)
    need(rc==0 and summary_exists_complete(job,180),condition+'が安全停止/中断しました')
    print('P012_STAGE_COMPLETE '+condition,flush=True)

def launch(root):
    host();verify_installed(root)
    with open('/var/lock/cpucond-p01275-launch.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        marker=root/'active-unit.txt'
        if marker.exists():
            old=read(marker).decode().strip()
            if live(state(old)):print('P012_CHAIN_ALREADY_RUNNING unit='+old,flush=True);return
        statuspath=root/'status.json'
        if statuspath.exists():
            s=load(statuspath)
            if s.get('phase')=='P012_ALL_COMPLETE':print('P012_CHAIN_ALREADY_COMPLETE',flush=True);return
            need(s.get('phase')!='BLOCKED','連鎖は安全上の理由で停止しています。原因確認前に自動再起動しません')
        unit='cpucond75-p012-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.service'
        text_atomic(marker,unit+'\n');setstatus(root,'STARTING',unit=unit)
        command(['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
            '--property=RuntimeMaxSec=infinity','--property=MemoryMax=512M','--property=TasksMax=32',
            '--property=TimeoutStopSec=20','--property=KillMode=control-group','--property=CPUAffinity=24',
            '--property=Nice=19','--property=StandardOutput=append:'+str(root/'chain.log'),
            '--property=StandardError=append:'+str(root/'chain.log'),'--setenv=CPUCOND_CHAIN_UNIT='+unit,
            '--setenv=PYTHONDONTWRITEBYTECODE=1','/usr/bin/python3','-B','-u',str(root/'control/goal0075_p012_chain.py'),
            '--chain-worker','--root',str(root)],stdin=subprocess.DEVNULL)
        print('P012_CHAIN_STARTED\nunit='+unit+'\nroot='+str(root),flush=True)
        print('P0→P1→P2。現在の処理は中断しません。全体時間上限なし、API課金なし、サーバー契約は継続。',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--enable',action='store_true');mode.add_argument('--chain-worker',action='store_true');mode.add_argument('--stage-worker',action='store_true')
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--condition',choices=CONDITIONS)
    args=parser.parse_args();root=args.root
    try:
        need(root==ROOT and root.resolve()==ROOT,'連鎖先のパスが違います');host()
        if args.enable:
            kit=Path(__file__).resolve().parent;verify_tree(kit,'DISTRIBUTION_SHA256SUMS')
            with open('/var/lock/cpucond-p01275-prepare.lock','a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if root.exists():prepare(root,kit,None,None)
                else:
                    need(importlib.metadata.version('tokenizers')=='0.21.4','計数ライブラリの固定版が違います')
                    audit=load(AUDIT/'report/summary.json');need(audit['observed_count_mismatches']==0,'以前のトークン監査が不一致')
                    need(digest(read(AUDIT/'tokenizer.json'))==audit['tokenizer_sha256'],'トークナイザー不一致')
                    from tokenizers import Tokenizer
                    tokenizer=Tokenizer.from_file(str(AUDIT/'tokenizer.json'));tokenizer.no_truncation();tokenizer.no_padding()
                    prepare(root,kit,tokenizer,capture_hardware())
                f=finish74(root);f.install(P0,root/'control/finish74')
                text_atomic('/root/goal0075-current-chain.path',str(root)+'\n')
            launch(root)
        elif args.chain_worker:orchestrate(root)
        else:stage_worker(root,args.condition)
        return 0
    except Exception as exc:
        if root==ROOT and root.exists():
            # An admission error in a repeated --enable must not overwrite a running controller status.
            if not args.enable:
                try:setstatus(root,'BLOCKED',error=type(exc).__name__+': '+str(exc),failed_condition=args.condition)
                except Exception:pass
        print('P012_CHAIN_BLOCKED: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True);return 1
if __name__=='__main__':raise SystemExit(main())
