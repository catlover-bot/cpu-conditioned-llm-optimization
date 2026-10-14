"""Pure, offline GPU006 backup semantics; never execute archived/generated code.

Reader contract: read(repo_relative_path, cap=...), exists(path), iter_paths(prefix).
The nested checkpoint checks match the original read_archive/pathname rules,
read as inert text from byte-pinned evaluator source; no source is imported.
"""
from __future__ import annotations
import argparse, ast, gzip, hashlib, io, json, math, os, stat, statistics, tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

MIB=1024**2
PLAN='runs/gpu006-target-info-v1/inputs/plan.json'
PLAN_SHA='9f5570a6b8d87b90df9eee97fba56fb33311e8d52cb93e1d9f17248b37c64a83'
QROOT='runs/gpu006-qwen-experiment-v1/results/l4'
CROOT='runs/gpu006-cloud180-v1/results/l4'
CLOUD='runs/gpu006-cloud180-v1'
REFERENCE='runs/gpu006-target-info-v1/inputs/reference'
PINS={
 'runs/gpu006-tools-v1/cudacond_gpu006_prepare_l4_v1.py':'427675e790429706ba7854b00229be07a26c67183ea4698c80baa5cff6866e2c',
 'runs/gpu006-qwen-experiment-tools-v1/cudacond_gpu006_qwen_generate_measure_v1.py':'b73557497936fa6a68bb6b90e9c2b8a9e8b81c46ea4d04159c31013aadd86bf1',
 'runs/gpu006-qwen-direct-ssh-tools-v1/cudacond_gpu006_qwen90_direct_ssh_v1.py':'ba3a71089f003af0d5041668e6f6fb8486fe8f97b8d6da1f1b61ed416ebf394c',
 'runs/gpu006-migration-tools-v1_1/cudacond_gpu006_rebind_l4_v1_1.py':'19b6882daf983400ddd94f9905811863541aca0e20d0c73e7bc961c27d5b47b4'}
SMALL={
 'gemm':[[1,1,1],[7,13,11],[17,33,19]], 'gesummv':[[1,1,1],[17,17,1],[257,257,1]],
 'syrk':[[1,1,1],[7,13,1],[33,17,1]], 'syr2k':[[1,1,1],[7,13,1],[33,17,1]],
 'convolution-2d':[[1,1,1],[7,13,1],[33,17,1]], 'convolution-3d':[[1,1,1],[5,7,9],[9,17,33]]}
TOOLS=('memcheck','initcheck','racecheck','synccheck')
FLAGS=['--gpu-architecture=sm_89','--std=c++17','--fmad=false','--ftz=false','--prec-div=true',
       '--prec-sqrt=true','--restrict','--generate-line-info','--device-stack-protector=true']

class AuditError(RuntimeError): pass

def need(ok,message):
    if not ok: raise AuditError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def parse(raw):
    def pairs(items):
        out={}
        for key,value in items:
            need(key not in out,'Duplicate JSON key')
            out[key]=value
        return out
    def bad(value): raise AuditError('Nonfinite JSON number')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=bad)

def pathname(name):
    need(isinstance(name,str),'Nonstring archive path')
    p=PurePosixPath(name)
    need(name and str(p)==name and not p.is_absolute() and '..' not in p.parts and '\\' not in name and '\x00' not in name,'Unsafe archive path')
    return p

class FilesystemReader:
    def __init__(self,root): self.root=Path(os.path.abspath(root))
    def read(self,name,cap=256*MIB):
        pathname(name)
        path=self.root/name
        for part in (path,*path.parents): need(not part.is_symlink(),'Symlink file refused')
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        with os.fdopen(fd,'rb') as stream:
            info=os.fstat(stream.fileno())
            need(stat.S_ISREG(info.st_mode) and info.st_size<=cap,'Not a bounded regular file')
            raw=stream.read(cap+1)
        need(len(raw)<=cap,'Read cap exceeded')
        return raw
    def exists(self,name):
        pathname(name)
        return (self.root/name).is_file() and not (self.root/name).is_symlink()
    def iter_paths(self,prefix):
        pathname(prefix)
        return sorted(str(path.relative_to(self.root)) for path in (self.root/prefix).rglob('*') if path.is_file() and not path.is_symlink())

def read_archive(raw,receipt,cap=256*MIB,manifest_name='CHECKPOINT_SHA256.json'):
    need(isinstance(receipt,dict),'Missing receipt')
    need(len(raw)==receipt.get('bytes') and sha(raw)==receipt.get('sha256'),'Archive hash/size differs')
    total=0
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        while True:
            chunk=stream.read(MIB)
            if not chunk: break
            total+=len(chunk)
            need(total<=cap,'Gzip expansion exceeds bound')
    files={};used=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive:
            pathname(member.name)
            need(member.isfile() and not member.issym() and not member.islnk() and member.size<=64*MIB,'Nonregular/oversized tar member')
            need(member.name not in files,'Duplicate tar member')
            used+=member.size
            need(used<=cap and len(files)<20000,'Archive limits exceeded')
            raw_member=archive.extractfile(member).read(member.size+1)
            need(len(raw_member)==member.size,'Truncated tar member')
            files[member.name]=raw_member
    manifest_raw=files.pop(manifest_name,None)
    need(manifest_raw is not None,'Missing archive manifest')
    if manifest_name=='CHECKPOINT_SHA256.json': need(sha(manifest_raw)==receipt.get('manifest_sha256'),'Manifest hash differs')
    need(parse(manifest_raw)=={name:sha(value) for name,value in files.items()},'Internal archive hashes differ')
    if manifest_name=='CHECKPOINT_SHA256.json': need(len(files)==receipt.get('files'),'Archive member count differs')
    return files

def index(items,expected,label):
    need(isinstance(items,list),label+' is not a list')
    ids=[item['id'] for item in items]
    need(len(ids)==len(set(ids)) and set(ids)==set(expected),label+' ID coverage differs')
    return {item['id']:item for item in items}

def bundle(files,prefix):
    for tail in ('job.json','numeric-result.json','parent-result.json','process.log'):
        need(prefix+'/'+tail in files,'Missing raw job/log: '+prefix+'/'+tail)
    return parse(files[prefix+'/numeric-result.json']),parse(files[prefix+'/job.json'])

def timing(files,prefix,task,shape,block):
    result,job=bundle(files,prefix)
    need(job['task']==task and job['shape']==shape and job['block']==block,'Timing job identity differs')
    rows=result.get('rows')
    need(result.get('ok') is True and isinstance(rows,list) and len(rows)==16,'Missing raw timing pairs')
    keys=set()
    for row in rows:
        session,pair=row['session'],row['pair']
        need(type(session) is int and type(pair) is int and session in (0,1) and pair in range(8),'Timing grid differs')
        keys.add((session,pair))
        need(row['order']==([0,1] if (session+pair)%2==0 else [1,0]),'AB/BA order differs')
        need(type(row['repeats']) is int and 1<=row['repeats']<=128,'Timing repetition bound differs')
        for field in ('baseline_ms','candidate_ms','ratio'):
            need(type(row[field]) in (int,float) and math.isfinite(row[field]) and row[field]>0,'Invalid raw time/ratio')
        need(math.isclose(row['ratio'],row['baseline_ms']/row['candidate_ms'],rel_tol=1e-12,abs_tol=0),'Raw timing quotient differs')
    need(len(keys)==16,'Duplicate raw timing cell')
    return len(rows)


def timing_metric(rows):
    ratios=[row['ratio'] for row in rows]
    median=statistics.median(ratios)
    quartiles=statistics.quantiles(ratios,n=4,method='inclusive')
    relative_iqr=(quartiles[2]-quartiles[0])/median
    sessions=[statistics.median([row['ratio'] for row in rows if row['session']==session]) for session in range(2)]
    reasons=[]
    if relative_iqr>0.1: reasons.append('paired_ratio_relative_iqr')
    if abs(math.log(sessions[0]/sessions[1]))>math.log(1.03): reasons.append('between_session_ratio_change')
    return {'speedup':median,'relative_iqr':relative_iqr,'session_medians':sessions,'quality_reasons':reasons,'measurement_valid':not reasons}

def verify_metric(files,prefix,recorded):
    metric=timing_metric(parse(files[prefix+'/timing/numeric-result.json'])['rows'])
    identity=timing_metric(parse(files[prefix+'/identity-timing/numeric-result.json'])['rows'])
    if not identity['measurement_valid'] or abs(math.log(identity['speedup']))>math.log(1.02):
        metric['measurement_valid']=False
        metric['quality_reasons'].append('identity_control_shift')
    for key,value in metric.items(): need(recorded.get(key)==value,'Raw timing metric recomputation differs: '+prefix+' '+key)
    need(recorded.get('identity')==identity,'Raw identity metric recomputation differs')
    need(recorded.get('speedup_gt_1_02')==(metric['measurement_valid'] and metric['speedup']>1.02),'Recorded speedup threshold differs')
    return metric

def stats(values):
    values=list(values)
    return {'n':len(values),'geometric_mean':math.exp(sum(math.log(x) for x in values)/len(values)) if values else None,
            'min':min(values) if values else None,'max':max(values) if values else None,'gt_1_02':sum(x>1.02 for x in values)}

def close_stats(actual,recorded):
    need(set(actual)<=set(recorded),'Principal aggregate fields missing')
    for key,value in actual.items():
        if type(value) is float: need(type(recorded[key]) in (int,float) and math.isclose(value,recorded[key],rel_tol=1e-13,abs_tol=1e-15),'Principal aggregate differs: '+key)
        else: need(recorded[key]==value,'Principal aggregate differs: '+key)


def submitted_payloads(reader,manifest):
    drafts={}
    for provider in ('openai','anthropic'):
        for trial in (1,2,3):
            suffix='jsonl' if provider=='openai' else 'json'
            path=f'runs/gpu006-target-info-v1/inputs/drafts/trial-{trial:02d}/{provider}-requests-NOT-SUBMITTED.{suffix}'
            drafts[f'{provider}-trial-{trial:02d}']=(path,reader.read(path,4*MIB))
    result={}
    for batch in manifest['operational_batches']:
        source,raw=drafts[batch['source_batch_key']]
        if batch['key']=='openai-pilot' or batch['key'].endswith('-remainder'):
            lines=raw.splitlines(keepends=True)
            chosen=[line for line in lines if (parse(line)['custom_id'] in set(batch['ids']))]
            raw=b''.join(chosen)
        result[batch['key']]=raw
        need(sha(raw)==batch['body_sha256'],'Actual submitted payload hash differs')
    return result

def audit_reader(reader):
    """Deterministic pure-reader semantic audit, including actual archived failures."""
    plan_raw=reader.read(PLAN,4*MIB)
    need(sha(plan_raw)==PLAN_SHA,'Fixed plan SHA changed')
    plan=parse(plan_raw);requests={item['id']:item for item in plan['requests']}
    need(len(requests)==len(plan['requests'])==270,'Fixed270 scope differs')
    need(Counter(item['provider'] for item in requests.values())=={'qwen':90,'openai':90,'anthropic':90},'Provider90 scopes differ')
    for path,wanted in PINS.items(): need(sha(reader.read(path,4*MIB))==wanted,'Original implementation pin differs')
    core=reader.read(REFERENCE+'/numeric-core.py',4*MIB)
    need(sha(core)==plan['numerical_core_sha256'],'Numerical core pin differs')
    reference={task:reader.read(REFERENCE+'/sources/'+task+'.cu',MIB) for task in plan['tasks']}
    for row in requests.values(): need(sha(reference[row['task']])==row['original_source_sha256'],'Original CUDA pin differs')
    for name in ('LICENSE','upstream/LICENSE','upstream-manifest.json','numeric-protocol.json'):
        need(bool(reader.read(REFERENCE+'/'+name,4*MIB)),'Required reference/license missing')
    inventory=[];cache={};counts=Counter();candidate_rows=[];invalid=[];all_outcomes=[];run_rows=[];measurement_rows=[]
    def archive(root,label):
        key=root+'/'+label
        if key not in cache:
            raw=reader.read(key+'.tar.gz',256*MIB);receipt_raw=reader.read(key+'-receipt.json',MIB);receipt=parse(receipt_raw)
            files=read_archive(raw,receipt);cache[key]=files
            inventory.append({'path':key+'.tar.gz','receipt_path':key+'-receipt.json','sha256':sha(raw),'bytes':len(raw),
                              'receipt_sha256':sha(receipt_raw),'manifest_sha256':receipt['manifest_sha256'],'files':len(files),
                              'raw_cuda_members':sum(n.endswith('.cu') for n in files),'ptx_members':sum(n.endswith('.ptx') for n in files),
                              'cubin_members':sum(n.endswith('.cubin') for n in files),'compile_logs':sum(n.endswith('/compile.log') for n in files),
                              'process_logs':sum(n.endswith('/process.log') for n in files),'numeric_results':sum(n.endswith('/numeric-result.json') for n in files)})
        return cache[key]
    for kind,root,expected_count in (('qwen',QROOT,90),('cloud',CROOT,180)):
        summary=archive(root,'summary');setup=archive(root,'setup')
        need(summary['plan.json']==setup['plan.json']==plan_raw,'Checkpoint fixed plan differs')
        protocol=parse(summary['protocol.json']);groups=protocol['candidate_groups'];metadata=parse(summary['summary.json'])
        expected_ids={rid for rid,row in requests.items() if (row['provider']=='qwen')==(kind=='qwen')}
        outcomes=index(parse(summary['outcomes.json']),expected_ids,kind+' summary')
        need(len(outcomes)==expected_count,'Run outcome scope differs')
        all_outcomes.extend(outcomes.values())
        group_ids=[rid for group in groups for rid in group['request_ids']]
        need(len(group_ids)==len(set(group_ids))==expected_count and set(group_ids)==expected_ids,'Candidate group coverage differs')
        labels={'setup','original-controls','all-block-validation','frozen-selection','summary'}|{phase+'-'+task for phase in ('exploration','confirmation') for task in plan['tasks']}
        labels|={'evaluated-'+group['label'] for group in groups}
        labels|=({'generation-session'}|{'generated-'+group['label'] for group in groups}) if kind=='qwen' else {'readiness'}
        found={name[len(root)+1:-7] for name in reader.iter_paths(root) if name.startswith(root+'/') and '/' not in name[len(root)+1:] and name.endswith('.tar.gz')}
        need(len(labels)==54 and found==labels,'Exact54 checkpoint labels differ: '+kind)
        for label in sorted(labels): archive(root,label)
        environment=parse(setup['environment-before.json'])
        target=parse(summary['target.json'])
        need(metadata['gpu_uuid']==environment['identity']['gpu_uuid']==target['expected_gpu_uuid'],'Execution GPU identity differs')
        for task in plan['tasks']: need(setup['sources/'+task+'.cu']==reference[task],'Archived original CUDA differs')
        original=archive(root,'original-controls');allblock=archive(root,'all-block-validation')
        for task in plan['tasks']:
            for shape in SMALL[task]+plan['performance_shapes'][task]:
                shape_name='x'.join(map(str,shape));prefix=task+'/'+shape_name
                baseline_sha=sha(original[prefix+'/baseline/kernel.cubin'])
                for arm in ('baseline','identity'):
                    raw,job=bundle(original,prefix+'/'+arm)
                    need(raw.get('ok') is True and raw['compile']['options']==FLAGS,'Original compile options differ')
                    need(reference[task].strip() in original[prefix+'/'+arm+'/kernel.cu'],'Original compiled source differs')
                    for suffix in ('ptx','cubin'):
                        need(prefix+'/'+arm+'/kernel.'+suffix in original,'Original compiled bytes missing')
                    need(prefix+'/'+arm+'/compile.log' in original,'Original compile log missing')
                    counts['original_control_compiled_shapes']+=1
                for arm in ('validation','alternate-block'):
                    raw,job=bundle(original,prefix+'/'+arm+'/bitwise')
                    need(raw['bitwise_pass'] is True and job['task']==task and job['shape']==shape and job['cubin_sha256']==baseline_sha,'Original validation input/source binding differs')
                    need([case['seed'] for case in raw['cases']]==[0,1009,9173],'Original input seed grid differs')
                    counts['original_control_bitwise_jobs']+=1
                if shape==SMALL[task][-1]:
                    for tool in TOOLS:
                        raw,job=bundle(original,prefix+'/validation/'+tool)
                        parent=parse(original[prefix+'/validation/'+tool+'/parent-result.json'])
                        need(parent['sanitizer_clean'] is True and raw['bitwise_pass'] is True and job['cubin_sha256']==baseline_sha,'Original sanitizer evidence differs')
                        counts['original_control_sanitizer_jobs']+=1
                if shape in plan['performance_shapes'][task]:
                    job=parse(original[prefix+'/identity-timing/job.json'])
                    counts['original_identity_raw_timing_rows']+=timing(original,prefix+'/identity-timing',task,shape,job['block'])
                for block in plan['allowed_blocks'][task]:
                    block_prefix=task+'/b'+'x'.join(map(str,block))+'/'+shape_name
                    raw,job=bundle(allblock,block_prefix+'/bitwise')
                    need(raw['bitwise_pass'] is True and job['task']==task and job['shape']==shape and job['block']==block and job['cubin_sha256']==baseline_sha,'All-block validation grid/source binding differs')
                    need([case['seed'] for case in raw['cases']]==[0,1009,9173],'All-block input seed grid differs')
                    counts['allblock_bitwise_jobs']+=1
                    if shape==SMALL[task][-1]:
                        for tool in TOOLS:
                            raw,job=bundle(allblock,block_prefix+'/'+tool)
                            parent=parse(allblock[block_prefix+'/'+tool+'/parent-result.json'])
                            need(parent['sanitizer_clean'] is True and raw['bitwise_pass'] is True and job['task']==task and job['shape']==shape and job['block']==block and job['cubin_sha256']==baseline_sha,'All-block sanitizer grid/source binding differs')
                            counts['allblock_sanitizer_jobs']+=1
        controls=parse(summary['controls.json']);selection=parse(summary['selection.json']);frozen=archive(root,'frozen-selection')
        need(parse(frozen['selection.json'])==selection,'Frozen selection differs')
        need(parse(frozen['exploration-rows.json'])==[r for r in controls if r['phase']=='exploration'],'Frozen exploration rows differ')
        grid={(phase,task,tuple(block),tuple(shape)) for phase in ('exploration','confirmation') for task in plan['tasks'] for block in plan['allowed_blocks'][task] for shape in plan['performance_shapes'][task]}
        actual=[(r['phase'],r['task'],tuple(r['block']),tuple(r['shape'])) for r in controls]
        need(len(actual)==len(set(actual))==176 and set(actual)==grid,'Control176 grid differs')
        for row in controls:
            files=archive(root,row['phase']+'-'+row['task']);prefix='b'+'x'.join(map(str,row['block']))+'/'+'x'.join(map(str,row['shape']))
            need(parse(files[prefix+'/outcome.json'])==row,'Raw control outcome differs')
            for mode in ('timing','identity-timing'):
                counts['control_raw_timing_rows']+=timing(files,prefix+'/'+mode,row['task'],row['shape'],row['block'] if mode=='timing' else row['reference_block'])
            verify_metric(files,prefix,row)
            counts['control_cells']+=1
            if not row['measurement_valid']: invalid.append({'run':kind,'kind':'control','task':row['task'],'phase':row['phase'],'block':row['block'],'shape':row['shape'],'quality_reasons':row['quality_reasons']})
        for task in plan['tasks']:
            scores=[]
            for block in plan['allowed_blocks'][task]:
                cells=[r for r in controls if r['phase']=='exploration' and r['task']==task and r['block']==block]
                need(len(cells)==2,'Exploration two-size coverage differs')
                if all(r['measurement_valid'] for r in cells):
                    scores.append({'block':block,'score':math.exp(sum(math.log(r['speedup']) for r in cells)/2)})
            recorded=selection[task]
            need(recorded['no_confirmation_data_used'] is True and len(recorded['eligible_scores'])==len(scores),'Frozen selection eligibility differs')
            for a,b in zip(scores,recorded['eligible_scores']):
                need(a['block']==b['block'] and math.isclose(a['score'],b['score'],rel_tol=1e-13),'Frozen selection score differs')
            selected=max(scores,key=lambda item:item['score'])
            need(recorded['selected_block']==selected['block'] and math.isclose(recorded['exploration_score'],selected['score'],rel_tol=1e-13),'Frozen selected block differs')
        need(metadata['valid_control_cells']==sum(r['measurement_valid'] for r in controls),'Run valid control aggregate differs')
        for group in groups:
            evaluated=archive(root,'evaluated-'+group['label'])
            mirrored=parse(evaluated['gpu006-outcomes.json'])
            need(mirrored==[outcomes[rid] for rid in group['request_ids']],'Group outcome mirror differs')
            generated=archive(root,'generated-'+group['label']) if kind=='qwen' else None
            for rid in group['request_ids']:
                row=requests[rid];outcome=outcomes[rid];condition=row['information_condition']
                for key in ('provider','model','task','trial','messages_sha256','original_source_sha256'):
                    need(outcome[key]==row[key],'Outcome identity differs: '+rid)
                need(outcome['condition']==condition,'Condition mapping differs')
                if outcome['generation_status']!='saved':
                    need(outcome['generation_status']=='invalid_generation' and outcome['stage']=='generation_failed' and outcome['correctness_passed'] is False and outcome.get('error'),'Missing invalid-generation reason')
                    need(not outcome.get('measurements') and not outcome.get('tuned_measurements'),'Invalid candidate has fabricated measurement')
                    invalid.append({'run':kind,'kind':'candidate','id':rid,'reason':outcome['error'],'raw_response_sha256':outcome['raw_response_sha256']})
                    counts['invalid_generation']+=1
                    continue
                source=evaluated['generation/'+condition+'/candidate.cu']
                need(sha(source)==outcome['source_sha256'],'Saved CUDA hash differs: '+rid)
                need(outcome['block'] in plan['allowed_blocks'][row['task']],'Saved BLOCK differs from fixed allowable set')
                need(outcome['correctness_passed'] is True,'Saved candidate numeric validation failed')
                if generated:
                    for tail in ('request.json','response.json','record.json','wire-request.json','intent.json','candidate.cu'):
                        name=condition+'/'+tail
                        need(evaluated['generation/'+name]==generated[name],'Qwen generation mirror differs')
                    need(parse(generated[condition+'/request.json'])==row,'Qwen actual request differs from fixed plan')
                    response=parse(generated[condition+'/response.json']);wire=parse(generated[condition+'/wire-request.json'])
                    need(response['model']==row['model'] and response['truncated'] is False,'Qwen raw response model/truncation differs')
                    header=next(line for line in response['content'].splitlines() if line.strip())
                    need(parse(header.encode())=={'block':outcome['block']} and source.decode().strip() in response['content'],'Qwen raw CUDA/BLOCK differs')
                    need(wire['seed']==row['seed'] and wire['n_predict']==8192,'Qwen actual seed/cap differs')
                    for key in ('temperature','top_p','min_p','top_k'): need(wire[key]==plan['generation_settings']['qwen'][key],'Qwen actual sampling differs')
                    counts['qwen_actual_requests']+=1;counts['qwen_raw_responses']+=1
                shapes=SMALL[row['task']]+plan['performance_shapes'][row['task']]
                need(set(outcome['compilation'])=={'x'.join(map(str,shape)) for shape in shapes},'Five compilation shape coverage differs')
                checks={tuple(item['bitwise']['shape']):item for item in outcome['checks']}
                need(len(checks)==5 and set(checks)=={tuple(shape) for shape in shapes},'Five validation shape coverage differs')
                for shape in shapes:
                    name='x'.join(map(str,shape));prefix='evaluation/'+condition+'/'+name;comp=outcome['compilation'][name]
                    for suffix in ('ptx','cubin'):
                        value=evaluated[prefix+'/compiled/kernel.'+suffix]
                        need(sha(value)==comp[suffix+'_sha256'] and len(value)==comp['compile'][suffix+'_bytes'],'Actual compiled bytes/hash differ')
                    need(source in evaluated[prefix+'/compiled/kernel.cu'],'Compiled CUDA does not contain saved candidate')
                    need(comp['ok'] is True and comp['compile']['options']==FLAGS,'Compile status/options differ')
                    bundle(evaluated,prefix+'/compiled');need(prefix+'/compiled/compile.log' in evaluated,'Missing compile log')
                    counts['candidate_compiled_shapes']+=1
                    bitwise,job=bundle(evaluated,prefix+'/validation/bitwise')
                    need(bitwise['bitwise_pass'] is True and [case['seed'] for case in bitwise['cases']]==[0,1009,9173],'Raw validation seed grid differs')
                    need(job['shape']==shape and job['task']==row['task'] and job['block']==outcome['block'] and job['cubin_sha256']==comp['cubin_sha256'],'Validation input/job binding differs')
                    counts['candidate_bitwise_jobs']+=1
                    check=checks[tuple(shape)]
                    need(check['passed'] is True and all(check['bitwise'].get(k)==v for k,v in bitwise.items()),'Recorded bitwise outcome differs')
                    needed=TOOLS if shape==SMALL[row['task']][-1] else ()
                    need(set(check['sanitizers'])==set(needed),'Four sanitizer tool coverage differs')
                    for tool in needed:
                        result,sjob=bundle(evaluated,prefix+'/validation/'+tool)
                        need(check['sanitizers'][tool]['sanitizer_clean'] is True and result['bitwise_pass'] is True and all(check['sanitizers'][tool].get(k)==v for k,v in result.items()),'Raw sanitizer outcome differs')
                        need(sjob['task']==row['task'] and sjob['shape']==shape and sjob['block']==outcome['block'] and sjob['cubin_sha256']==comp['cubin_sha256'],'Sanitizer input/job binding differs')
                        need(parse(evaluated[prefix+'/validation/'+tool+'/parent-result.json'])==check['sanitizers'][tool],'Sanitizer parent outcome differs')
                        need(b'0 errors' in evaluated[prefix+'/validation/'+tool+'/process.log'],'Clean sanitizer log absent')
                        need([case['seed'] for case in result['cases']]==[0,1009,9173],'Sanitizer seed grid differs')
                        counts['candidate_sanitizer_jobs']+=1
                for field,baseline in (('measurements','original'),('tuned_measurements','frozen_selected')):
                    metrics=outcome[field]
                    need(len(metrics)==2 and {tuple(x['shape']) for x in metrics}=={tuple(x) for x in plan['performance_shapes'][row['task']]},'Two performance size coverage differs')
                    for metric in metrics:
                        prefix='evaluation/'+condition+'/'+'x'.join(map(str,metric['shape']))+('/selected-reference' if field=='tuned_measurements' else '')
                        counts['candidate_raw_timing_rows']+=timing(evaluated,prefix+'/timing',row['task'],metric['shape'],outcome['block'])
                        identity=parse(evaluated[prefix+'/identity-timing/job.json'])
                        counts['candidate_raw_timing_rows']+=timing(evaluated,prefix+'/identity-timing',row['task'],metric['shape'],identity['block'])
                        verify_metric(evaluated,prefix,metric)
                        measurement_rows.append({'id':rid,'provider':row['provider'],'task':row['task'],'trial':row['trial'],'condition':condition,'shape':metric['shape'],'baseline':baseline,'measurement_valid':metric['measurement_valid'],'speedup':metric['speedup']})
                        counts['candidate_measurement_cells']+=1
                        if metric['measurement_valid']: counts['candidate_valid_measurement_cells']+=1
                        else: invalid.append({'run':kind,'kind':'measurement','id':rid,'baseline':baseline,'shape':metric['shape'],'quality_reasons':metric['quality_reasons']})
                counts['saved_candidates']+=1
                candidate_rows.append({'id':rid,'provider':row['provider'],'task':row['task'],'condition':condition,'trial':row['trial'],
                                       'source_sha256':sha(source),'block':outcome['block'],'evaluated_archive':root+'/evaluated-'+group['label']+'.tar.gz'})
        for baseline,field in (('original','valid_original_comparisons'),('frozen_selected','valid_tuned_comparisons')):
            need(metadata[field]==sum(m['measurement_valid'] for m in measurement_rows if m['baseline']==baseline and (m['provider']=='qwen')==(kind=='qwen')),'Run valid timing aggregate differs')
        run_rows.append({'run':kind,'archive_count':54,'planned_ids':expected_count,'saved_candidates':sum(x['generation_status']=='saved' for x in outcomes.values()),
                         'invalid_generation':sum(x['generation_status']=='invalid_generation' for x in outcomes.values()),'summary':metadata,'selection':selection,
                         'environment':environment,'numeric_protocol':protocol['numeric_protocol']})
    need(counts['saved_candidates']==255 and counts['invalid_generation']==15,'Exact255saved/15invalid coverage differs')
    collected=index(parse(reader.read(CLOUD+'/results/collected.json',16*MIB)),{rid for rid,row in requests.items() if row['provider']!='qwen'},'Cloud provider results')
    payload=index(parse(reader.read(CLOUD+'/worker-candidates.json',16*MIB)),set(collected),'Cloud worker candidate payload')
    manifest=parse(reader.read(CLOUD+'/execution-manifest.json',4*MIB));ledger=parse(reader.read(CLOUD+'/state/ledger.json',4*MIB))
    need(manifest['fixed_plan_sha256']==PLAN_SHA and sha(canonical(manifest))==ledger['execution_manifest_sha256'],'Operational manifest binding differs')
    submitted=submitted_payloads(reader,manifest);raw_id_coverage=[];submissions=[]
    for batch in manifest['operational_batches']:
        entry=ledger['batches'][batch['key']]
        need(entry['status']=='COLLECTED' and entry['ids']==batch['ids'] and entry['body_sha256']==sha(submitted[batch['key']]),'Seven actual submissions differ')
        intent=parse(reader.read(CLOUD+'/state/intents/'+batch['key']+'.json',MIB))
        need(intent['actual_body_sha256']==entry['body_sha256'] and intent['ids']==entry['ids'],'Submitted intent binding differs')
        normalized_raw=reader.read(CLOUD+'/'+entry['normalized_path'],16*MIB)
        need(sha(normalized_raw)==entry['normalized_sha256'],'Normalized result digest differs')
        normalized=index(parse(normalized_raw),entry['ids'],'Batch normalized results')
        native={}
        for artifact in entry['raw_artifacts']:
            raw=reader.read(CLOUD+'/'+artifact['path'],16*MIB)
            need(sha(raw)==artifact['sha256'],'Raw native batch digest differs')
            for line in raw.splitlines():
                if not line.strip(): continue
                item=parse(line);rid=item['custom_id'];need(rid not in native,'Duplicate native ID');native[rid]=item
        need(set(native)==set(entry['ids']),'Raw native batch result coverage differs')
        raw_id_coverage+=list(native)
        status=entry['terminal_status_artifact'];need(sha(reader.read(CLOUD+'/'+status['path'],MIB))==status['sha256'],'Terminal Batch status hash differs')
        for rid,item in normalized.items():
            need(item==collected[rid] and item['generation_status']=='saved','Native generation collection mapping differs')
            outcome=next(x for x in all_outcomes if x['id']==rid)
            need(outcome['raw_response_sha256']==item['raw_response_sha256']==payload[rid]['raw_response_sha256'],'Candidate/native raw response hash binding differs')
            if outcome['generation_status']=='saved': need(payload[rid]['source_sha256']==outcome['source_sha256'] and payload[rid]['block']==outcome['block'],'Parsed source/BLOCK mapping differs')
            else: need(payload[rid]['generation_status']=='invalid_generation' and payload[rid]['error']==outcome['error'],'Invalid raw response reason mapping differs')
        submissions.append({'key':batch['key'],'provider':batch['provider'],'ids':batch['ids'],'body_sha256':entry['body_sha256'],'batch_id':entry['batch_id'],
                            'raw_artifacts':entry['raw_artifacts'],'terminal_status_artifact':status,'normalized_sha256':entry['normalized_sha256']})
    need(len(submissions)==7 and len(raw_id_coverage)==len(set(raw_id_coverage))==180,'Seven native batches/180 ID coverage differs')
    acceptance=ledger['pilot_acceptance'];need(sha(reader.read(CLOUD+'/'+acceptance['path'],4*MIB))==acceptance['sha256'],'API acceptance proof changed')
    approval=ledger['approval'];need(sha(reader.read(CLOUD+'/'+approval['path'],4*MIB))==approval['sha256'],'Approval changed')
    setup_root='runs/gpu006-qwen-setup-v1';setup_receipt=parse(reader.read(setup_root+'/receipt.json',MIB))
    setup_files=read_archive(reader.read(setup_root+'/evidence.tar.gz',256*MIB),setup_receipt,manifest_name='MANIFEST.json')
    model=parse(setup_files['evidence/model-identity.json']);runtime=parse(setup_files['evidence/runtime-identity.json']);qconfig=parse(setup_files['config.json'])
    generation=archive(QROOT,'generation-session');props=parse(generation['props.json']);template=props['chat_template']
    need(model['sha256']==qconfig['qwen']['model_sha256'] and model['bytes']==qconfig['qwen']['model_bytes'],'Model provenance differs')
    need(props['model_alias']==plan['generation_settings']['qwen']['id'],'Inference model alias differs')
    setup_source_path=setup_root+'/setup-runner.py'
    setup_source=reader.read(setup_source_path,4*MIB)
    constants={}
    def literal(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,int,float,bool)): return node.value
        if isinstance(node,ast.Name) and node.id in constants: return constants[node.id]
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
            left,right=literal(node.left),literal(node.right)
            if isinstance(left,str) and isinstance(right,str): return left+right
        raise ValueError('Not an inert supported literal')
    for node in ast.parse(setup_source).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: constants[node.targets[0].id]=literal(node.value)
            except ValueError: pass
    need(constants.get('MODEL_SHA')==model['sha256'] and constants.get('MODEL_BYTES')==model['bytes'],'Model source declaration differs')
    need(constants.get('COMMIT')==runtime['commit'],'llama.cpp source commit differs')
    need(isinstance(constants.get('BLOB_URL'),str) and constants['BLOB_URL'].endswith(model['sha256']),'Exact model source URL missing')
    sources=[{'path':setup_source_path,'field':'BLOB_URL','url':constants['BLOB_URL'],'source_sha256':sha(setup_source)},
             {'path':setup_source_path,'field':'REPO','url':constants['REPO'],'source_sha256':sha(setup_source)}]
    provenance={'model_id':props['model_alias'],'model_identity':model,'model_source_records':sorted(sources,key=lambda x:(x['path'],x['field'],x['url'])),
                'runtime_identity':runtime,'server_command':parse(generation['server-command.json']),'props_sha256':sha(generation['props.json']),
                'chat_template_sha256':sha(template.encode()),'full_chat_template_member':QROOT+'/generation-session.tar.gz::props.json',
                'native_generation_settings':plan['generation_settings']['qwen'],'initial_setup_archive':setup_root+'/evidence.tar.gz',
                'runtime_binaries_in_setup_archive':False,'cmake_cache_bytes_in_setup_archive':False,
                'runtime_capture_status':'Separate remote runtime archive must report whether remaining actual binaries/libraries/CMake/source were captured; hashes alone are not those bytes.'}
    need(provenance['chat_template_sha256']==parse(setup_files['report.json'])['smoke']['template_sha256'],'Exact chat template provenance differs')
    pointer=parse(reader.read(CLOUD+'/analysis/latest.json',MIB))
    analysis_raw=reader.read(CLOUD+'/'+pointer['report_path'],16*MIB)
    need(sha(analysis_raw)==pointer['snapshot_sha256'],'Latest analysis snapshot hash differs')
    analysis=parse(analysis_raw)
    fully_valid=sum(o['correctness_passed'] is True and all(m['measurement_valid'] for field in ('measurements','tuned_measurements') for m in o.get(field,[])) for o in all_outcomes)
    need(analysis['planned_slots']==270 and analysis['processing_terminal_slots']==270 and analysis['successful_l4_candidate_slots']==fully_valid==253 and analysis['A40_columns'] is None,'Principal full270/253/A40 aggregate differs')
    principal=[]
    for model in analysis['models']:
        provider=model['provider']
        record={'provider':provider,'baselines':{},'contrasts':[]}
        valid=[m for m in measurement_rows if m['provider']==provider and m['measurement_valid']]
        for baseline in ('original','frozen_selected'):
            aggregate=stats(m['speedup'] for m in valid if m['baseline']==baseline)
            close_stats(aggregate,model['conditional_performance_on_valid_size_cells'][baseline])
            record['baselines'][baseline]=aggregate
        lookup={(m['task'],m['trial'],tuple(m['shape']),m['baseline'],m['condition']):m for m in valid}
        for contrast in model['primary_within_model_contrasts']:
            left,right=contrast['contrast'].split('/')
            baseline=contrast['baseline'];ratios=[];tasks=[]
            for task in plan['tasks']:
                current=[]
                for trial in (1,2,3):
                    for shape in plan['performance_shapes'][task]:
                        a=lookup.get((task,trial,tuple(shape),baseline,left));b=lookup.get((task,trial,tuple(shape),baseline,right))
                        if a and b: current.append(a['speedup']/b['speedup'])
                ratios+=current
                if len(current)==6: tasks.append(stats(current)['geometric_mean'])
            close_stats(stats(ratios),contrast['conditional_cell_stats'])
            equal_task=stats(tasks)['geometric_mean']
            need(contrast['valid_matched_size_cells']==len(ratios) and contrast['tasks_with_all_six_pairs']==len(tasks),'Principal matched contrast coverage differs')
            need(equal_task is None and contrast['equal_task_geometric_mean_on_fully_matched_tasks'] is None or equal_task is not None and math.isclose(equal_task,contrast['equal_task_geometric_mean_on_fully_matched_tasks'],rel_tol=1e-13),'Principal equal-task condition contrast differs')
            record['contrasts'].append({'contrast':contrast['contrast'],'baseline':baseline,'valid_cells':len(ratios),'fully_matched_tasks':len(tasks),'equal_task_geometric_mean':equal_task})
        principal.append(record)
    coverage={'planned_ids':270,'saved_candidates':255,'invalid_generation':15,'qwen_archive_count':54,'cloud_archive_count':54,
              'candidate_compiled_shapes':counts['candidate_compiled_shapes'],'candidate_bitwise_jobs':counts['candidate_bitwise_jobs'],
              'candidate_sanitizer_jobs':counts['candidate_sanitizer_jobs'],'candidate_measurement_cells':counts['candidate_measurement_cells'],
              'candidate_valid_measurement_cells':counts['candidate_valid_measurement_cells'],'candidate_raw_timing_rows':counts['candidate_raw_timing_rows'],
              'control_cells':counts['control_cells'],'control_raw_timing_rows':counts['control_raw_timing_rows'],
              'original_control_compiled_shapes':counts['original_control_compiled_shapes'],'original_control_bitwise_jobs':counts['original_control_bitwise_jobs'],
              'original_control_sanitizer_jobs':counts['original_control_sanitizer_jobs'],'allblock_bitwise_jobs':counts['allblock_bitwise_jobs'],
              'allblock_sanitizer_jobs':counts['allblock_sanitizer_jobs'],'original_identity_raw_timing_rows':counts['original_identity_raw_timing_rows'],
              'qwen_actual_requests':counts['qwen_actual_requests'],'qwen_raw_responses':counts['qwen_raw_responses'],'cloud_native_raw_ids':180,'actual_submitted_batches':7}
    return {'schema':'gpu006-offline-backup-semantic-audit-v1','coverage_complete':True,'plan_sha256':PLAN_SHA,'coverage':coverage,
            'archives':sorted(inventory,key=lambda x:x['path']),'runs':run_rows,'saved_candidates':sorted(candidate_rows,key=lambda x:x['id']),
            'principal_aggregates_recomputed':principal,'principal_analysis_reference':{'path':CLOUD+'/'+pointer['report_path'],'sha256':sha(analysis_raw)},
            'invalid_records':sorted(invalid,key=lambda x:json.dumps(x,sort_keys=True)),'submissions':sorted(submissions,key=lambda x:x['key']),
            'inference_provenance':provenance,'validation_input_storage':{'form':'byte-pinned numerical-core plus exact shapes, seeds, job bindings and expected live-out hashes',
              'serialized_array_dumps_stored':False,'input_data_seeds':[0,1009,9173],'timing_seed':4327,'gpu_revalidation_performed':False},
            'required_source_roots':['runs/gpu006-target-info-v1','runs/gpu006-qwen-experiment-v1','runs/gpu006-qwen-setup-v1',CLOUD,*sorted({str(PurePosixPath(p).parent) for p in PINS})],
            'limitations':['Offline preservation verification only; no generation, compilation, sanitizer execution, GPU timing or provider API calls.',
                           'Model weights are excluded by default. Exact model hash/bytes/ID/source and inference settings/template/commit are retained.',
                           'Actual runtime binary/library/CMake bytes are a separately captured archive when still present; local setup identities alone do not establish their preservation.']}

def audit_repository(repo): return audit_reader(FilesystemReader(repo))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=audit_repository(args.repo);raw=canonical(result)
    if args.output:
        path=Path(os.path.abspath(args.output));allowed=Path(os.path.abspath(args.repo))/'runs/gpu006-backup-v1'
        need(path.is_relative_to(allowed),'Audit report output must stay under backup run')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(json.dumps({'coverage_complete':True,'coverage':result['coverage']},sort_keys=True))