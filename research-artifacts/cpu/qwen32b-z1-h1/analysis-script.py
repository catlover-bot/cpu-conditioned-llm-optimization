#!/usr/bin/env python3
"""Stage16E: read-only audit/statistics of completed Stage16D.

No candidate execution, compilation, model calls, network requests or timing.
Read the completed source tree; publish analysis and selected evidence to a NEW
output tree. The archive is not a replacement for the full experimental backup.
Kernel-cluster bootstrap retains all sizes of each sampled kernel. It reports
both group-weighted and equal-kernel estimands; it does not resample generation
seeds, establish equivalence, or infer a population of all programs.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import statistics
import sys
import tarfile
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True
SOURCE = Path('/srv/research/cpucond-qwen-z1h1-stage16d-v1')
OUTPUT = Path('/srv/research/cpucond-qwen-z1h1-stage16e-v1')
D_RUNNER_SHA = 'e65e54306b9edf5c0f726e295b6eac05068f3ea69ebc98f6b67bf8bb4eca75cc'
D_MANIFEST_SHA = 'ecd6cce0f6c0ae9e9c32278fdde8479512ad491400e953402f7bb1696376b7e9'
COMPLETE = 'QWEN_Z1_H1_PERFORMANCE_COMPLETE'
SCHEMA = 'qwen-z1-h1-readonly-statistics-v1'
CID_RE = re.compile(r'^([A-Za-z0-9_-]+)__(MINI|SMALL|MEDIUM)__C__(P1|H1)__s0$')
HEX_RE = re.compile(r'^[0-9a-f]{64}$')
LIMIT = 64 * 1024**2

class Refuse(RuntimeError):
    pass

def need(x, message):
    if not x:
        raise Refuse(message)

def canon(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')

def decode(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            need(k not in out, 'duplicate JSON key: ' + k)
            out[k] = v
        return out
    def bad(x):
        raise Refuse('nonfinite JSON: ' + x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def sha_file(p):
    need(p.is_file() and not p.is_symlink(), 'not a regular file: ' + str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''):
            h.update(b)
    return h.hexdigest()

def safe(root, relative):
    need(isinstance(relative, str) and relative and '\\' not in relative and '\x00' not in relative,
         'invalid relative path')
    p = PurePosixPath(relative)
    need(not p.is_absolute() and '..' not in p.parts and p.as_posix() != '.', 'unsafe relative path')
    root = Path(root).resolve()
    q = root
    for part in p.parts:
        q = q / part
        need(not q.is_symlink(), 'symlink refused: ' + str(q))
    need(q.resolve().is_relative_to(root), 'outside source root')
    return q

def positive(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0

def close(a, b):
    return positive(a) and positive(b) and math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-13)

def identity(cid):
    m = CID_RE.fullmatch(cid)
    need(m is not None, 'invalid candidate ID: ' + str(cid))
    return {'task': m[1], 'size': m[2], 'form': 'C', 'condition': m[3]}

class Evidence:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.verified = {}
        self.selected = {}
    def read(self, rel, select=True):
        p = safe(self.root, rel)
        need(p.is_file() and p.stat().st_size <= LIMIT, 'missing/oversized evidence: ' + str(p))
        raw = p.read_bytes()
        need(len(raw) <= LIMIT, 'evidence grew too large')
        r = {'bytes': len(raw), 'sha256': sha(raw)}
        if rel in self.verified:
            need(self.verified[rel] == r, 'evidence changed during audit: ' + rel)
        self.verified[rel] = r
        if select:
            self.selected[rel] = raw
        return raw
    def json(self, rel, select=True):
        return decode(self.read(rel, select))
    def check_file(self, rel, expected, size=None, select=False):
        raw = self.read(rel, select)
        need(sha(raw) == expected, 'SHA mismatch: ' + rel)
        if size is not None:
            need(len(raw) == size, 'size mismatch: ' + rel)
        return raw
    def object_hash(self, path, expected):
        p = Path(path)
        need(p.is_absolute() and p.is_relative_to(self.root), 'object path outside source tree')
        rel = p.relative_to(self.root).as_posix()
        p = safe(self.root, rel)
        need(sha_file(p) == expected, 'native object hash mismatch: ' + rel)
        self.verified[rel] = {'bytes': p.stat().st_size, 'sha256': expected}


def matched_from_outcomes(outcomes):
    bykey = defaultdict(dict)
    for row in outcomes:
        spec = identity(row['id'])
        need(all(row.get(k) == v for k,v in spec.items()), 'outcome identity mismatch')
        key = (row['task'], row['size'])
        c = row['condition']
        need(c not in bykey[key], 'duplicate outcome arm')
        bykey[key][c] = row
    matched = []
    for (task,size),arms in sorted(bykey.items()):
        need(set(arms) == {'P1','H1'}, 'missing outcome arm')
        if not all(arms[c]['measurement_valid'] for c in ('P1','H1')):
            continue
        z,h = arms['P1'],arms['H1']
        need(positive(z['speedup']) and positive(h['speedup']), 'invalid speedup')
        need(z['baseline_object_sha256'] == h['baseline_object_sha256'], 'paired baseline differs')
        need(HEX_RE.fullmatch(z['candidate_object_sha256']) is not None, 'bad object digest')
        need(HEX_RE.fullmatch(h['candidate_object_sha256']) is not None, 'bad object digest')
        matched.append({'task':task,'size':size,'form':'C','Z1':z['speedup'],'H1':h['speedup'],
            'Z1_over_H1':z['speedup']/h['speedup'],
            'same_candidate_source':z['source_sha256']==h['source_sha256'],
            'same_native_object':z['candidate_object_sha256']==h['candidate_object_sha256'],
            'Z1_id':z['id'],'H1_id':h['id']})
    return matched


def stock_interpretation(rec):
    need(type(rec.get('passed')) is bool, 'stock gate boolean missing')
    a,b = rec.get('reference_stdout_sha256'),rec.get('candidate_stdout_sha256')
    need(isinstance(a,str) and HEX_RE.fullmatch(a), 'bad oracle digest')
    need(isinstance(b,str) and HEX_RE.fullmatch(b), 'bad stdout digest')
    empty = b == sha(b'')
    equal = a == b
    if rec['passed']:
        need(rec['execution_state']=='ok' and equal and not empty, 'inconsistent stock pass')
        classification='stock_output_pass'
    elif rec['execution_state']!='ok':
        classification='execution_failure'
    elif empty:
        classification='normal_exit_but_empty_stdout'
    elif not equal:
        classification='normal_exit_but_stdout_digest_differs'
    else:
        raise Refuse('stock gate failure inconsistent with recorded digests')
    return {'classification':classification,'candidate_stdout_empty':empty,
            'stdout_digests_equal':equal,
            'cause_within_code_harness_or_serialization':'not_determined_by_this_audit'}


def audit(root, manifest_sha=D_MANIFEST_SHA, runner_sha=D_RUNNER_SHA):
    """Hashes are production anchors; injection arguments are for local fixture tests only."""
    ev=Evidence(root)
    ev.check_file('control/runner.py',runner_sha,select=True)
    summary=ev.json('summary.json')
    expected=ev.read('summary.json.sha256').decode().split()[0]
    need(expected==sha(ev.selected['summary.json']), 'summary sidecar mismatch')
    need(summary.get('completion')==COMPLETE,'Stage16D incomplete')
    required={'requests_total':180,'correctness_pass_eligible':144,'measurement_terminal':144,
              'measurement_pending':0,'measurement_valid':136,'timing_retries':0}
    for k,v in required.items():
        need(summary.get(k)==v, 'summary count changed: '+k)
    need(summary.get('historical_performance_values_used') is False,'historical timing was used')
    manifest=ev.json('inputs/manifest.json')
    need(sha(canon(manifest))==manifest_sha==summary['input_manifest_sha256'],'input manifest changed')
    fmap={}
    for e in manifest['files']:
        need(e['path'] not in fmap,'duplicate input manifest path')
        fmap[e['path']]=e
        ev.check_file('inputs/'+e['path'],e['sha256'],e['bytes'],False)
    rows=manifest['candidates']; byid={r['id']:r for r in rows}
    need(len(rows)==len(byid)==180,'candidate inventory dimensions')
    hashes=ev.json('outcome-hashes.json')
    need(set(hashes)==set(byid),'outcome hash ID set mismatch')
    outcomes=[]
    for cid in sorted(byid):
        o=decode(ev.check_file('outcomes/'+cid+'.json',hashes[cid],select=True))
        r=byid[cid]
        need(o['id']==cid and o['source_sha256']==r['source_sha256'],'outcome source identity mismatch')
        need(type(o.get('stage16c_correctness_pass')) is bool and type(o.get('measurement_valid')) is bool,
             'invalid outcome boolean')
        need(o['stage16c_correctness_pass']==r['correctness_passed'],'eligibility mismatch')
        need(o['speedup'] is None or positive(o['speedup']),'invalid outcome speedup')
        ev.check_file('inputs/'+r['performance_source'],r['source_sha256'],select=True)
        outcomes.append(o)
    jl=[decode(ln) for ln in ev.read('outcomes.jsonl').splitlines() if ln.strip()]
    need(len(jl)==180 and {x['id']:x for x in jl}=={x['id']:x for x in outcomes},'outcome JSONL disagrees')
    eligible=[o for o in outcomes if o['stage16c_correctness_pass']]
    need(Counter(o['condition'] for o in eligible)=={'P1':71,'H1':73},'eligibility counts')
    good=[o for o in outcomes if o['measurement_valid']]
    need(Counter(o['condition'] for o in good)=={'P1':67,'H1':69},'valid counts')
    need(len(list((ev.root/'measurement').glob('*/result.json')))==144,'measurement file count')
    gates=[]; quality=[]; all_reasons=Counter()
    plan=ev.json('inputs/package/plan.json')
    insts={(i['task'],i['size']):i for i in plan['instances_list']}
    for o in eligible:
        cid=o['id']; z=ev.json('measurement/'+cid+'/result.json')
        need(z['id']==cid and z['measurement_valid']==o['measurement_valid'],'measurement flags disagree')
        need(z.get('speedup')==o['speedup'] and z.get('errors',[])==o['errors'],'measurement/outcome disagree')
        if 'rows' in z:
            need(len(z['rows'])==16,'timing trial count changed')
            for trial in z['rows']:
                need(positive(trial['reference_ns']) and positive(trial['candidate_ns']) and positive(trial['batch']),
                     'invalid raw timing')
                need(close(trial['speedup'],trial['reference_ns']/trial['candidate_ns']),'raw speedup inconsistency')
        elif o['measurement_valid']:
            raise Refuse('measurement-valid without raw trials')
        st=ev.json('candidate-native/'+cid+'/stock-check.json')
        need(st['id']==cid and st['source_sha256']==o['source_sha256'],'stock identity')
        meaning=stock_interpretation(st)
        if o['measurement_valid']:
            need(st['passed'],'timed candidate failed stock output gate')
            nr=ev.json('candidate-native/'+cid+'/result.json')
            need(nr['source_sha256']==o['source_sha256'],'native receipt source identity')
            need(nr['native_object_sha256']==o['candidate_object_sha256']==z['candidate_object_sha256'],
                 'native object receipts differ')
            ev.object_hash(nr['native_object'],nr['native_object_sha256'])
        if not o['measurement_valid']:
            all_reasons.update(o['quality_reasons'])
            record={k:o.get(k) for k in ('id','task','size','condition','stage','speedup','errors','quality_reasons')}
            record['stock_check']=st
            record['stock_interpretation']=meaning
            if not st['passed']:
                need(o['stage']=='native_candidate_gate' and o['speedup'] is None,'failed output gate timed')
                record['evidence_files']=[]
                directory=ev.root/'candidate-native'/cid
                # Saved diagnostics only, not executing or rebuilding the candidate.
                for p in sorted(directory.rglob('*')):
                    if not p.is_file() or p.is_symlink():
                        continue
                    if p.name.startswith(('stock-check','kernel')) and (
                        p.suffix in {'.json','.txt','.log','.stdout','.stderr','.bin','.out'}):
                        if p.stat().st_size<=LIMIT:
                            rel=p.relative_to(ev.root).as_posix()
                            raw=ev.read(rel)
                            record['evidence_files'].append({'path':rel,'bytes':len(raw),'sha256':sha(raw),
                                'matches_candidate_stdout':sha(raw)==st['candidate_stdout_sha256']})
                inst=insts[(o['task'],o['size'])]
                for rel in (inst['oracle'], inst['driver'], inst['sources']['C']['path']):
                    ev.read('inputs/package/'+rel)
                oracle=ev.read('inputs/package/'+inst['oracle'])
                need(sha(oracle)==st['reference_stdout_sha256'],'stock oracle changed')
                record['oracle_bytes']=len(oracle)
                rel='inputs/correctness/results/'+cid+'.json'
                rec=ev.json(rel)
                need(rec['passed'] is True, 'stock failure was not Stage16C pass')
                record['previous_stage16c_pass']=True
                gates.append(record)
            else:
                record['stage_category']='timing_quality_or_control'
                quality.append(record)
    need(len(gates)==7 and len(quality)==1,'unexpected failure categories')
    need(dict(all_reasons)==summary['invalid_reason_occurrences'],'invalid reasons do not reproduce')
    pairs=matched_from_outcomes(outcomes)
    persisted=ev.json('matched-Z1-H1.json')
    need(persisted['groups']==pairs and persisted['correctness_eligible_groups']==70,'persisted pairing disagrees')
    ms=summary['matched_Z1_H1']
    need(len(pairs)==ms['measurement_valid_groups']==66,'matched count')
    need(len({p['task'] for p in pairs})==ms['unique_kernels']==23,'matched kernels')
    need(sum(p['same_candidate_source'] for p in pairs)==ms['same_candidate_source_groups']==57,'same source count')
    need(sum(p['same_native_object'] for p in pairs)==ms['same_native_object_groups']==63,'same object count')
    for c,k in [('Z1','Z1_geomean_speedup'),('H1','H1_geomean_speedup'),('Z1_over_H1','Z1_over_H1_geomean_ratio')]:
        need(close(geomean(p[c] for p in pairs),ms[k]),'matched headline not reproduced: '+k)
    for c in ('P1','H1'):
        vals=[o['speedup'] for o in good if o['condition']==c]
        need(close(geomean(vals),summary['by_condition'][c]['geomean_speedup_valid']),'condition headline')
    # Preserve exact numerical-comparison code as text, never import it.
    ev.read('inputs/package/goal0069_batch_codegen.py')
    ev.read('inputs/package/utilities/polybench.c')
    ev.read('inputs/package/utilities/polybench.h')
    for rel in ('control/live-cgroup.json','control/protocol.json','control/launch.json','run.log','matched-Z1-H1.csv'):
        if safe(ev.root,rel).is_file():
            ev.read(rel)
    return ev,summary,outcomes,pairs,{'native_stock_output_failures':gates,'timing_quality_failures':quality,
                                   'reason_occurrences':dict(all_reasons)}


def geomean(xs):
    xs=list(xs)
    need(all(positive(x) for x in xs),'geomean input')
    return math.exp(statistics.fmean(math.log(x) for x in xs)) if xs else None

def pct(xs,q):
    need(xs and 0<=q<=1,'bad percentile')
    pos=(len(xs)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    return xs[lo]+(xs[hi]-xs[lo])*(pos-lo)

def describe(pairs):
    rs=[p['Z1_over_H1'] for p in pairs]
    return {'groups':len(rs),'kernels':len({p['task'] for p in pairs}),
        'geomean_Z1_over_H1':geomean(rs),'median_Z1_over_H1':statistics.median(rs) if rs else None,
        'min_ratio':min(rs) if rs else None,'max_ratio':max(rs) if rs else None,
        'Z1_wins':sum(r>1 for r in rs),'H1_wins':sum(r<1 for r in rs),'exact_ties':sum(r==1 for r in rs),
        'within_2pct_count':sum(1/1.02<=r<=1.02 for r in rs),
        'within_2pct_interpretation':'descriptive only; not an equivalence test'}

def cluster_bootstrap(pairs,reps,seed):
    groups=defaultdict(list)
    for p in pairs:groups[p['task']].append(math.log(p['Z1_over_H1']))
    vals=[groups[k] for k in sorted(groups)]
    need(len(vals)>=2 and reps>=1000,'insufficient bootstrap clusters/repetitions')
    sums=[sum(v) for v in vals]; ns=[len(v) for v in vals]; means=[statistics.fmean(v) for v in vals]
    k=len(vals);rng=random.Random(seed);gw=[];kb=[]
    for _ in range(reps):
        selected=[rng.randrange(k) for _j in range(k)]
        gw.append(math.exp(sum(sums[j] for j in selected)/sum(ns[j] for j in selected)))
        kb.append(math.exp(sum(means[j] for j in selected)/k))
    gw.sort();kb.sort()
    return {'repetitions':reps,'seed':seed,'resampling_unit':'kernel; keep all matched sizes together',
        'represented_kernels':k,
        'group_weighted':{'point':geomean(p['Z1_over_H1'] for p in pairs),'percentile_95_ci':[pct(gw,.025),pct(gw,.975)]},
        'equal_kernel_weighted':{'point':math.exp(statistics.fmean(means)),
                                 'percentile_95_ci':[pct(kb,.025),pct(kb,.975)]},
        'scope':'Conditional descriptive benchmark resampling, not generation-seed uncertainty or proof of zero effect.'}

def statistics_report(pairs,reps,seed):
    same=[p for p in pairs if p['same_native_object']]
    changed=[p for p in pairs if not p['same_native_object']]
    n=len(pairs)
    contributions={}
    for name,pp in [('same_native_object',same),('different_native_object',changed)]:
        contribution=sum(math.log(p['Z1_over_H1']) for p in pp)/n
        contributions[name]={'groups':len(pp),'mean_log_ratio_contribution_to_all_groups':contribution,
                             'multiplicative_contribution':math.exp(contribution)}
    kernels=sorted({p['task'] for p in pairs}); loko=[]
    for k in kernels:
        keep=[p for p in pairs if p['task']!=k]
        loko.append({'omitted_kernel':k,'groups_left':len(keep),'ratio':geomean(p['Z1_over_H1'] for p in keep)})
    tab=Counter((p['same_candidate_source'],p['same_native_object']) for p in pairs)
    return {'matched_all':describe(pairs),'kernel_cluster_bootstrap':cluster_bootstrap(pairs,reps,seed),
            'same_native_object':describe(same),'different_native_object':describe(changed),
            'different_native_object_rows':changed,'log_effect_decomposition':contributions,
            'source_object_cross_table':[{'same_source':s,'same_object':o,'groups':num} for (s,o),num in sorted(tab.items())],
            'leave_one_kernel_out':loko,
            'per_kernel':{k:describe([p for p in pairs if p['task']==k]) for k in kernels},
            'per_size':{s:describe([p for p in pairs if p['size']==s]) for s in ('MINI','SMALL','MEDIUM')},
            'guardrails':[
                'Retain all 66 matched pairs as main descriptive estimand; do not remove identical objects to inflate effects.',
                'Only 3 matched pairs differ at native-object level; that subgroup is descriptive, not independent confirmatory evidence.',
                'Identical kernel object bytes do not assert identical final executable layout or identical timings.',
                'Same-object timing differences are diagnostics, not automatically estimates that may be subtracted from other effects.',
                'The 7 stock output gate failures are not timing-noise exclusions; their underlying cause remains to be audited.',
                'No causal, equivalence, CPU-portability, or all-program population claim follows from this analysis.',
                'Previous Claude and present Qwen runs use different valid cohorts and not identical additional gates/timing schedules.'
            ]}


def write_new(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw)

def execute(source,out,reps,seed):
    source=source.resolve();out=out.resolve()
    need(not out.is_relative_to(source) and not source.is_relative_to(out),'analysis output overlaps evidence')
    archive=Path(str(out)+'.tgz');side=Path(str(archive)+'.sha256')
    for p in (out,archive,side):need(not p.exists() and not p.is_symlink(),'refusing overwrite: '+str(p))
    print('STAGE16E_READING_COMPLETED_DATA (no execution or timing)',flush=True)
    ev,s,rows,pairs,failures=audit(source)
    print('STAGE16E_SOURCE_AUDIT=PASS',flush=True)
    stats=statistics_report(pairs,reps,seed)
    result={'schema':SCHEMA,'completion':'QWEN_Z1_H1_READONLY_ANALYSIS_COMPLETE',
            'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source_stage16d_summary_sha256':sha(ev.selected['summary.json']),
            'stage16d_runner_sha256':D_RUNNER_SHA,'input_manifest_sha256':D_MANIFEST_SHA,
            'requests_total':180,'correctness_pass_eligible':144,'valid_performance_records':136,
            'native_stock_output_failed_candidates':7,'timing_quality_failed_candidates':1,
            'statistics':stats,'failure_details':failures,
            'candidate_executions':0,'new_measurements':0,'model_calls':0,'api_calls':0,'network_calls':0,
            'new_api_cost_usd':'0','source_tree_modified':False,
            'archive_scope':'Selected verified metadata, source code and gate diagnostics; not a full binary experiment backup.'}
    # Recheck hashes before publishing a fixed selected evidence set.
    for rel,meta in ev.verified.items():
        p=safe(source,rel)
        need(p.stat().st_size==meta['bytes'] and sha_file(p)==meta['sha256'], 'source changed during analysis: '+rel)
    out.mkdir(parents=True,exist_ok=False)
    write_new(out/'summary.json',canon(result))
    write_new(out/'failure-details.json',canon(failures))
    write_new(out/'matched-Z1-H1.json',canon({'groups':pairs}))
    write_new(out/'verified-source-files.json',canon(ev.verified))
    for rel,raw in sorted(ev.selected.items()):write_new(out/'evidence'/rel,raw)
    write_new(out/'analysis-script.py',Path(__file__).read_bytes())
    txt=(f"Matched pairs: {len(pairs)}; kernels: {stats['matched_all']['kernels']}\n"
         f"Z1/H1: {stats['matched_all']['geomean_Z1_over_H1']:.12g}\n"
         f"Kernel-cluster 95% interval (group-weighted): {stats['kernel_cluster_bootstrap']['group_weighted']['percentile_95_ci']}\n"
         f"Same native objects: {stats['same_native_object']['groups']}; different: {stats['different_native_object']['groups']}\n"
         "Stock-output gate failures: 7; timing-quality failures: 1. Do not conflate these.\n"
         "All original results retained. No candidate execution, new timing, or model call.\n")
    write_new(out/'report.txt',txt.encode())
    files=[p for p in sorted(out.rglob('*')) if p.is_file()]
    lines=''.join(sha_file(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in files)
    write_new(out/'SHA256SUMS',lines.encode('ascii'))
    with tarfile.open(archive,'x:gz',format=tarfile.PAX_FORMAT) as tf:tf.add(out,arcname=out.name)
    digest=sha_file(archive);write_new(side,(digest+'  '+archive.name+'\n').encode())
    compact={k:result[k] for k in ('completion','requests_total','correctness_pass_eligible',
              'valid_performance_records','native_stock_output_failed_candidates','timing_quality_failed_candidates',
              'candidate_executions','new_measurements','model_calls','api_calls')}
    compact.update(matched=stats['matched_all'],kernel_cluster_bootstrap=stats['kernel_cluster_bootstrap'],
        same_native_object=stats['same_native_object'],different_native_object=stats['different_native_object'],
        different_native_object_rows=stats['different_native_object_rows'],
        failure_ids={'native_stock_output':[r['id'] for r in failures['native_stock_output_failures']],
                     'timing_quality':[r['id'] for r in failures['timing_quality_failures']]},
        stock_failure_classifications=dict(Counter(r['stock_interpretation']['classification'] for r in failures['native_stock_output_failures'])),
        archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=digest,
        summary_sha256=sha_file(out/'summary.json'))
    print('=== STAGE16E COMPLETE ===',flush=True)
    print(json.dumps(compact,indent=2,ensure_ascii=False),flush=True)


def self_test():
    class Tests(unittest.TestCase):
        def test_safe_path(self):
            with tempfile.TemporaryDirectory() as d:
                for x in ('../x','/tmp/x','a/../../b','a\\b',''):
                    with self.assertRaises(Refuse):safe(d,x)
        def test_symlink(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'a').write_text('x');(p/'b').symlink_to(p/'a')
                with self.assertRaises(Refuse):safe(d,'b')
        def test_json(self):
            for raw in (b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":Infinity}'):
                with self.assertRaises(Refuse):decode(raw)
        def test_types(self):
            self.assertFalse(positive(True));self.assertFalse(positive(float('nan')))
            self.assertFalse(positive(0));self.assertTrue(positive(1))
        def test_id(self):
            self.assertEqual(identity('gemm__MINI__C__H1__s0')['condition'],'H1')
            with self.assertRaises(Refuse):identity('gemm__MINI__IR__H1__s0')
        def test_gmean(self):
            self.assertEqual(geomean([1,4]),2);self.assertIsNone(geomean([]))
        def test_percentile(self):
            self.assertEqual(pct([1,2,3],.25),1.5)
        def test_no_overwrite(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'x';write_new(p,b'a')
                with self.assertRaises(FileExistsError):write_new(p,b'b')
        def test_stock_ok_does_not_mean_output_equal(self):
            r={'passed':False,'execution_state':'ok','reference_stdout_sha256':sha(b'a'),
               'candidate_stdout_sha256':sha(b'b')}
            self.assertEqual(stock_interpretation(r)['classification'],'normal_exit_but_stdout_digest_differs')
        def test_stock_empty(self):
            r={'passed':False,'execution_state':'ok','reference_stdout_sha256':sha(b'a'),'candidate_stdout_sha256':sha(b'')}
            self.assertEqual(stock_interpretation(r)['classification'],'normal_exit_but_empty_stdout')
        def test_stock_inconsistent_pass(self):
            r={'passed':True,'execution_state':'ok','reference_stdout_sha256':sha(b'a'),'candidate_stdout_sha256':sha(b'b')}
            with self.assertRaises(Refuse):stock_interpretation(r)
        def test_bootstrap_constant(self):
            ps=[{'task':k,'Z1_over_H1':2.0} for k in ('a','b','b')]
            x=cluster_bootstrap(ps,1000,7)
            for name in ('group_weighted','equal_kernel_weighted'):
                self.assertTrue(all(abs(v-2)<1e-12 for v in x[name]['percentile_95_ci']))
        def test_estimands_differ(self):
            ps=[{'task':'a','Z1_over_H1':1.0}]*3+[{'task':'b','Z1_over_H1':4.0}]
            x=cluster_bootstrap(ps,1000,9)
            self.assertAlmostEqual(x['group_weighted']['point'],math.sqrt(2))
            self.assertAlmostEqual(x['equal_kernel_weighted']['point'],2)
        def test_bootstrap_seed(self):
            ps=[{'task':'a','Z1_over_H1':1.1},{'task':'b','Z1_over_H1':.9}]
            self.assertEqual(cluster_bootstrap(ps,1000,8),cluster_bootstrap(ps,1000,8))
        def test_matched_selection(self):
            rows=[]
            for k in ('a','b'):
                for c in ('P1','H1'):
                    rows.append({'id':f'{k}__MINI__C__{c}__s0','task':k,'size':'MINI','form':'C','condition':c,
                      'measurement_valid':not(k=='b' and c=='H1'),'speedup':1.0,'source_sha256':'a'*64,
                      'candidate_object_sha256':'b'*64,'baseline_object_sha256':'c'*64})
            self.assertEqual(len(matched_from_outcomes(rows)),1)
        def test_diagnostic_decomposition(self):
            ps=[]
            for i in range(66):
                ps.append({'task':f'k{i%23}','size':('MINI','SMALL','MEDIUM')[i%3],
                    'Z1_over_H1':1.001 if i<63 else 1.02,'same_native_object':i<63,'same_candidate_source':i<57})
            x=statistics_report(ps,1000,5)
            d=x['log_effect_decomposition']
            self.assertAlmostEqual(d['same_native_object']['multiplicative_contribution']*
                                   d['different_native_object']['multiplicative_contribution'],x['matched_all']['geomean_Z1_over_H1'])
            self.assertEqual(x['different_native_object']['groups'],3)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    need(result.wasSuccessful(),'self-test failed')
    print('STAGE16E_SELFTEST=PASS')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test',action='store_true');g.add_argument('--analyze',action='store_true')
    ap.add_argument('--input',type=Path,default=SOURCE);ap.add_argument('--out',type=Path,default=OUTPUT)
    ap.add_argument('--bootstrap-reps',type=int,default=50000);ap.add_argument('--seed',type=int,default=20260919)
    args=ap.parse_args()
    if args.self_test:self_test();return
    need(10000<=args.bootstrap_reps<=1000000,'bootstrap reps outside 10000..1000000')
    execute(args.input,args.out,args.bootstrap_reps,args.seed)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STAGE16E_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr)
        raise SystemExit(1)
