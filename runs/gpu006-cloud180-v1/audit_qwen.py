#!/usr/bin/env python3
"""Read-only audit of the immutable GPU006 Qwen90 L4 checkpoints.

Uses the byte-pinned original archive validator, CUDA output parser and timing
quality calculation. No archive extraction, HTTP, SSH, compiler or GPU execution.
All writes are deterministic derived reports within the new cloud180 directory.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import stat
import sys

PLAN_SHA = '9f5570a6b8d87b90df9eee97fba56fb33311e8d52cb93e1d9f17248b37c64a83'
PINS = {
 'runs/gpu006-tools-v1/cudacond_gpu006_prepare_l4_v1.py': '427675e790429706ba7854b00229be07a26c67183ea4698c80baa5cff6866e2c',
 'runs/gpu006-qwen-experiment-tools-v1/cudacond_gpu006_qwen_generate_measure_v1.py': 'b73557497936fa6a68bb6b90e9c2b8a9e8b81c46ea4d04159c31013aadd86bf1',
 'runs/gpu006-qwen-direct-ssh-tools-v1/cudacond_gpu006_qwen90_direct_ssh_v1.py': 'ba3a71089f003af0d5041668e6f6fb8486fe8f97b8d6da1f1b61ed416ebf394c',
 'runs/gpu006-migration-tools-v1_1/cudacond_gpu006_rebind_l4_v1_1.py': '19b6882daf983400ddd94f9905811863541aca0e20d0c73e7bc961c27d5b47b4',
}
SUMMARY_RECEIPT = {'bytes': 294977, 'files': 11,
 'sha256': 'ba67e98a8b1e9cdca2718f00c87da6e1aa403e7b587aa34c704906dc825abc76',
 'manifest_sha256': '33b8497136919632c39eab39d3aa7aec8e58d421c8cced0d4ca2951caf260fad'}
MIB = 1024**2
CONTRASTS = ('L4_NAME/NONE', 'L4_SPEC/NONE', 'L4_NAME/A40_NAME', 'L4_SPEC/A40_SPEC')

class AuditError(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise AuditError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)+'\n').encode()

def read(path, cap=256*MIB):
    p = Path(os.path.abspath(path))
    for part in (p, *p.parents):
        require(not part.is_symlink(), 'Symlink refused: '+str(part))
    fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_size <= cap, 'Not a bounded regular file: '+str(p))
        data = f.read(cap+1)
    require(len(data) <= cap, 'Read cap exceeded')
    return data

def load_legacy(repo_root):
    root = Path(os.path.abspath(repo_root))
    for name, expected in PINS.items():
        require(digest(read(root/name, 4*MIB)) == expected, 'Legacy implementation pin differs: '+name)
    path = root/'runs/gpu006-qwen-experiment-tools-v1/cudacond_gpu006_qwen_generate_measure_v1.py'
    spec = importlib.util.spec_from_file_location('gpu006_qwen_read_only_audit_legacy', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # This imports definitions and verifies embedded support bytes; no main() call.
    exec(compile(read(path, 4*MIB), str(path), 'exec'), module.__dict__)
    return module

def write_derived(path, data):
    p = Path(os.path.abspath(path))
    for part in (p, *p.parents):
        require(not part.is_symlink(), 'Output symlink refused')
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        require(read(p) == data, 'Existing derived report differs; retained: '+str(p))
        return
    with p.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def stats(values):
    xs = list(values)
    require(all(type(x) in (int, float) and x > 0 and math.isfinite(x) for x in xs), 'Invalid speed ratio')
    return {'n':len(xs), 'geometric_mean': math.exp(sum(math.log(x) for x in xs)/len(xs)) if xs else None,
            'min':min(xs) if xs else None, 'max':max(xs) if xs else None,
            'gt_1_02':sum(x > 1.02 for x in xs)}

def as_csv(rows):
    if not rows:
        return b''
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k:json.dumps(v, separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    return stream.getvalue().encode()

def recompute_metric(legacy, files, prefix, recorded):
    numeric = legacy.parse(files[prefix+'/timing/numeric-result.json'])
    identity = legacy.parse(files[prefix+'/identity-timing/numeric-result.json'])
    require(numeric.get('ok') is True and identity.get('ok') is True, 'Raw timing execution was not successful')
    for item in (numeric, identity):
        for row in item['rows']:
            require(row['baseline_ms'] > 0 and row['candidate_ms'] > 0, 'Nonpositive raw timing')
            require(row['ratio'] == row['baseline_ms']/row['candidate_ms'], 'Raw timing ratio differs from durations')
    metric = legacy.P.timing_metric(numeric['rows'])
    im = legacy.P.timing_metric(identity['rows'])
    if not im['measurement_valid'] or abs(math.log(im['speedup'])) > math.log(1.02):
        metric['measurement_valid'] = False
        metric['quality_reasons'].append('identity_control_shift')
    for name, value in metric.items():
        require(recorded[name] == value, 'Raw timing recomputation differs for '+prefix+' field '+name)
    require(recorded['identity'] == im, 'Raw identity metric differs: '+prefix)
    return {'timing_member':prefix+'/timing/numeric-result.json',
            'identity_member':prefix+'/identity-timing/numeric-result.json',
            'numeric_sha256':digest(files[prefix+'/timing/numeric-result.json']),
            'identity_sha256':digest(files[prefix+'/identity-timing/numeric-result.json']),
            'paired_rows':len(numeric['rows']), 'identity_paired_rows':len(identity['rows'])}

def run_audit(repo_root: Path, output_dir: Path | None = None) -> dict:
    """Audit old artifacts without mutating them; optionally write derived reports."""
    repo = Path(os.path.abspath(repo_root))
    legacy = load_legacy(repo)
    plan_bytes = read(repo/'runs/gpu006-target-info-v1/inputs/plan.json', 4*MIB)
    require(digest(plan_bytes) == PLAN_SHA, 'Fixed plan SHA-256 differs')
    plan = legacy.parse(plan_bytes)
    requests = {r['id']:r for r in plan['requests'] if r['provider']=='qwen'}
    require(len(requests)==90, 'Qwen request coverage differs')
    old = repo/'runs/gpu006-qwen-experiment-v1/results/l4'
    inventory = []
    def archive(label):
        raw = read(old/(label+'.tar.gz'))
        receipt_raw = read(old/(label+'-receipt.json'), MIB)
        receipt = legacy.parse(receipt_raw)
        if label=='summary':
            require(all(receipt.get(k)==v for k,v in SUMMARY_RECEIPT.items()), 'User-provided summary receipt differs')
        files = legacy.G.read_archive(raw, receipt)
        if not any(r['label']==label for r in inventory):
            inventory.append({'label':label, 'archive_sha256':digest(raw), 'receipt_sha256':digest(receipt_raw),
                              'manifest_sha256':receipt['manifest_sha256'], 'bytes':len(raw), 'files':len(files)})
        return files
    summary_files = archive('summary')
    require(summary_files['plan.json']==plan_bytes, 'Archived plan differs from fixed source plan')
    summary = legacy.parse(summary_files['summary.json'])
    outcomes = legacy.parse(summary_files['outcomes.json'])
    controls = legacy.parse(summary_files['controls.json'])
    selection = legacy.parse(summary_files['selection.json'])
    protocol = legacy.parse(summary_files['protocol.json'])
    target = legacy.parse(summary_files['target.json'])
    require(target['expected_gpu_uuid']==summary['gpu_uuid'], 'Summary GPU UUID differs')
    outcome_by_id = {r['id']:r for r in outcomes}
    require(len(outcomes)==len(outcome_by_id)==90 and set(outcome_by_id)==set(requests), 'Qwen90 outcome ID coverage differs')
    expected_labels = legacy.labels(legacy.qwen_groups(plan))
    require(len(expected_labels)==54, 'Checkpoint plan changed')
    require({p.stem for p in old.glob('*.tar.gz')}=={x+'.tar' for x in expected_labels}, 'Unexpected/missing checkpoint archive')
    originals = {task:read(repo/('runs/gpu006-target-info-v1/inputs/reference/sources/'+task+'.cu'), MIB).decode()
                 for task in plan['tasks']}
    baseline_files = archive('original-controls')
    baseline_hashes = {}
    for name, data in baseline_files.items():
        if name.endswith('/baseline/kernel.cubin') or name.endswith('/baseline/kernel.ptx'):
            parts = name.split('/')
            baseline_hashes[(parts[0],parts[1],parts[-1])] = digest(data)
    invalid_controls = []
    control_evidence = []
    for phase in ('exploration','confirmation'):
        for task in plan['tasks']:
            files = archive(phase+'-'+task)
            for row in (r for r in controls if r['phase']==phase and r['task']==task):
                prefix = 'b'+'x'.join(map(str,row['block']))+'/'+'x'.join(map(str,row['shape']))
                require(legacy.parse(files[prefix+'/outcome.json'])==row, 'Control checkpoint outcome differs')
                evidence = recompute_metric(legacy,files,prefix,row)
                evidence.update(archive=phase+'-'+task+'.tar.gz', phase=phase,task=task,block=row['block'],shape=row['shape'])
                control_evidence.append(evidence)
                if not row['measurement_valid']:
                    impact = ('Block is ineligible because both exploration sizes must be valid; selection remains '+str(selection[task]['selected_block'])
                              if phase=='exploration' else 'Confirmation is never used for selection; frozen selection remains '+str(selection[task]['selected_block']))
                    invalid_controls.append(dict(row, raw_evidence=evidence, selection_impact=impact))
    grid={(phase,t,tuple(b),tuple(sh)) for phase in ('exploration','confirmation') for t in plan['tasks']
          for b in plan['allowed_blocks'][t] for sh in plan['performance_shapes'][t]}
    seen=[(r['phase'],r['task'],tuple(r['block']),tuple(r['shape'])) for r in controls]
    require(len(controls)==len(set(seen))==176 and set(seen)==grid, 'Control grid differs')
    recomputed_selection=legacy.G.select_exploration([r for r in controls if r['phase']=='exploration'],protocol)
    require(recomputed_selection==selection, 'Frozen selection differs from original selection rule')
    frozen = archive('frozen-selection')
    require(legacy.parse(frozen['selection.json'])==selection, 'Frozen selection checkpoint differs')
    require(legacy.parse(frozen['exploration-rows.json'])==[r for r in controls if r['phase']=='exploration'], 'Frozen exploration rows differ')
    request_audit=[]
    measurement_rows=[]
    compiled_rows=[]
    raw_evidence=[]
    generation_tokens={'input_native_tokens':0,'output_native_tokens':0,'backend':'llama.cpp /completion; never used as cloud token counts'}
    for group in legacy.qwen_groups(plan):
        generated=archive('generated-'+group['label'])
        evaluated=archive('evaluated-'+group['label'])
        require(legacy.parse(evaluated['gpu006-outcomes.json'])==[outcome_by_id[x] for x in group['request_ids']], 'Evaluated checkpoint outcomes differ')
        for cid in group['request_ids']:
            row=requests[cid]
            outcome=outcome_by_id[cid]
            condition=row['information_condition']
            require(legacy.parse(generated[condition+'/request.json'])==row, 'Saved request differs from fixed plan: '+cid)
            for field in ('provider','model','task','information_condition','trial','seed','messages_sha256','original_source_sha256'):
                require(outcome[field]==row[field], 'Outcome mapping differs: '+cid+' '+field)
            require(outcome['condition']==condition and outcome['correctness_passed'] is True, 'Outcome condition/correctness differs')
            response=legacy.parse(generated[condition+'/response.json'])
            require(response['model']==row['model'] and response['truncated'] is False and response['stop_type'] in ('eos','word'), 'Native generation completion differs')
            source,block=legacy.G.parse_candidate(response['content'],row['task'],originals)
            source_bytes=generated[condition+'/candidate.cu']
            require(source_bytes==source.encode()==originals[row['task']].encode(), 'Raw candidate source differs from original: '+cid)
            require(block==outcome['block'] and digest(source_bytes)==outcome['source_sha256']==row['original_source_sha256'], 'BLOCK/source hash differs')
            require(outcome['source_equals_original'] is True, 'Original source sameness record differs')
            record=legacy.parse(generated[condition+'/record.json'])
            require(all(outcome[k]==v for k,v in record.items()), 'Generation record differs from outcome')
            for name,data in generated.items():
                require(evaluated['generation/'+name]==data, 'Generation mirror differs inside evaluated checkpoint')
            wire=legacy.parse(generated[condition+'/wire-request.json'])
            settings=plan['generation_settings']['qwen']
            require(wire['seed']==row['seed'] and wire['n_predict']==8192, 'Native request seed/output limit differs')
            for key in ('temperature','top_p','min_p','top_k'):
                require(wire[key]==settings[key], 'Native request sampling differs')
            intent=legacy.parse(generated[condition+'/intent.json'])
            require(intent['id']==cid and intent['attempt']==1 and intent['retry_allowed'] is False, 'Generation attempt record differs')
            generation_tokens['input_native_tokens']+=response['tokens_evaluated']
            generation_tokens['output_native_tokens']+=response['timings']['predicted_n']
            request_audit.append({k:row[k] for k in ('id','model','task','information_condition','trial','seed','messages_sha256','original_source_sha256')}|
                                 {'source_sha256':digest(source_bytes),'raw_source_equals_original':True,'block':block,
                                  'generation_status':outcome['generation_status'],'stage':outcome['stage'],'correctness_passed':True,
                                  'generated_archive':'generated-'+group['label']+'.tar.gz', 'evaluated_archive':'evaluated-'+group['label']+'.tar.gz'})
            for shape_name,recorded in outcome['compilation'].items():
                prefix='evaluation/'+condition+'/'+shape_name+'/compiled/'
                hashes={suffix:digest(evaluated[prefix+'kernel.'+suffix]) for suffix in ('ptx','cubin')}
                require(hashes['ptx']==recorded['ptx_sha256'] and hashes['cubin']==recorded['cubin_sha256'], 'Raw executable hash differs')
                baseline_match={suffix:hashes[suffix]==baseline_hashes[(row['task'],shape_name,'kernel.'+suffix)] for suffix in hashes}
                require(all(baseline_match.values()), 'Candidate executable differs from same-target original')
                compiled_rows.append({'id':cid,'task':row['task'],'condition':condition,'trial':row['trial'],'shape':shape_name,
                                      'ptx_sha256':hashes['ptx'],'cubin_sha256':hashes['cubin'],'same_ptx_as_original':True,'same_cubin_as_original':True})
            for kind in ('measurements','tuned_measurements'):
                require(len(outcome[kind])==2, 'Performance shape coverage differs')
                for metric in outcome[kind]:
                    shape='x'.join(map(str,metric['shape']))
                    prefix='evaluation/'+condition+'/'+shape+('/selected-reference' if kind=='tuned_measurements' else '')
                    evidence=recompute_metric(legacy,evaluated,prefix,metric)
                    evidence.update(id=cid,comparison=kind,archive='evaluated-'+group['label']+'.tar.gz')
                    raw_evidence.append(evidence)
                    job=legacy.parse(evaluated[prefix+'/timing/job.json'])
                    require(job['block']==block and job['shape']==metric['shape'] and job['task']==row['task'], 'Timing job metadata differs')
                    if kind=='tuned_measurements':
                        require(metric['reference_block']==selection[row['task']]['selected_block'], 'Tuned baseline is not frozen selection')
                        require(job['reference_block']==metric['reference_block'], 'Tuned raw timing baseline differs')
                    measurement_rows.append({'id':cid,'model':row['model'],'task':row['task'],'condition':condition,'trial':row['trial'],
                                             'shape':shape,'execution_target':'L4','baseline':'original' if kind=='measurements' else 'frozen_selected',
                                             'block':block,'reference_block':legacy.C.SPECS[row['task']]['base'] if kind=='measurements' else metric['reference_block'],
                                             'measurement_valid':metric['measurement_valid'],'speedup':metric['speedup'],
                                             'gt_1_02':metric['speedup_gt_1_02'],'raw_timing_archive':evidence['archive'], 'raw_timing_member':evidence['timing_member']})
    for label in expected_labels:
        if not any(r['label']==label for r in inventory):
            archive(label)
    valid=[r for r in measurement_rows if r['measurement_valid']]
    original=[r for r in valid if r['baseline']=='original']
    tuned=[r for r in valid if r['baseline']=='frozen_selected']
    fast=[r for r in original if r['speedup']>1.02]
    require(len(original)==summary['valid_original_comparisons']==180 and len(tuned)==summary['valid_tuned_comparisons']==180, 'Summary valid comparisons differ')
    require(len(fast)==summary['speedups_gt_1_02_vs_original']==15 and sum(r['speedup']>1.02 for r in tuned)==summary['speedups_gt_1_02_vs_tuned']==0, 'Summary speedup count differs')
    require(len(invalid_controls)==176-summary['valid_control_cells']==2, 'Summary invalid control count differs')
    per_task=[]
    for task in plan['tasks']:
        subset=[r for r in request_audit if r['task']==task]
        blocks=sorted({tuple(r['block']) for r in subset})
        require(len(subset)==15 and len(blocks)==1, 'Unexpected within-task BLOCK variation')
        per_task.append({'task':task,'slots':len(subset),'failure_slots':0,'unique_sources':len({r['source_sha256'] for r in subset}),
                         'blocks':[list(b) for b in blocks],'original_block':legacy.C.SPECS[task]['base'],'frozen_selected_block':selection[task]['selected_block'],
                         'original':stats(r['speedup'] for r in original if r['task']==task),
                         'frozen_selected':stats(r['speedup'] for r in tuned if r['task']==task)})
    pair_rows=[]
    contrast_stats=[]
    lookup={(r['task'],r['trial'],r['shape'],r['baseline'],r['condition']):r for r in valid}
    for contrast in CONTRASTS:
        left,right=contrast.split('/')
        for baseline in ('original','frozen_selected'):
            pair_subset=[]
            for task in plan['tasks']:
                for trial in plan['trials']:
                    for shape in plan['performance_shapes'][task]:
                        shape_id='x'.join(map(str,shape))
                        a=lookup.get((task,trial,shape_id,baseline,left))
                        b=lookup.get((task,trial,shape_id,baseline,right))
                        if a and b:
                            item={'contrast':contrast,'baseline':baseline,'model':summary['model'],'task':task,'trial':trial,
                                  'shape':shape_id,'execution_target':'L4','left_id':a['id'],'right_id':b['id'],
                                  'left_speedup':a['speedup'],'right_speedup':b['speedup'],'normalized_speed_ratio':a['speedup']/b['speedup']}
                            pair_rows.append(item)
                            pair_subset.append(item)
            tasks=[{'task':t,**stats(r['normalized_speed_ratio'] for r in pair_subset if r['task']==t)} for t in plan['tasks']]
            contrast_stats.append({'contrast':contrast,'baseline':baseline,'expected_pairs':36,'valid_pairs':len(pair_subset),
                                   'ratio_definition':'(baseline/left candidate)/(baseline/right candidate); ratio above 1 favors left',
                                   'cells':stats(r['normalized_speed_ratio'] for r in pair_subset),
                                   'task_means':tasks,'equal_task_geometric_mean':stats(t['geometric_mean'] for t in tasks)['geometric_mean']})
    condition_stats=[]
    for condition in plan['information_conditions']:
        condition_stats.append({'condition':condition,'planned_slots':18,'generation_failures':0,'correctness_failures':0,
                                'original':stats(r['speedup'] for r in original if r['condition']==condition),
                                'frozen_selected':stats(r['speedup'] for r in tuned if r['condition']==condition)})
    limitations=[
      'Read-only audit of archived real L4 data; this command performs no new generation, API submission, compilation or measurement.',
      'All 90 parsed CUDA sources equal their task original byte-for-byte. BLOCK is constant across the 15 condition/trial slots within each task. This is observed output behavior; it does not establish an LLM internal understanding.',
      'PTX and cubin equality was checked using actual bytes for every saved compilation and same-target baseline. Equality applies within a task and compile shape on this L4/runtime; executable hashes can differ across shapes and targets.',
      'The four condition comparisons pair task, trial, size, execution target and baseline. They divide separate baseline-normalized timings; they are not a direct timing run of one condition against another.',
      'The 1.02 threshold is a descriptive speedup threshold, not statistical significance. Six development tasks are the independent workload units; sizes, repeats and generation trials do not supply extra independent tasks.',
      'No formal equivalence, holdout generalization, model ranking or A40/L4 bidirectional adaptation is claimed. A40 candidate timings remain unmeasured.',
      'Qwen generation uses a local llama.cpp native completion backend. Native input/output usage cannot be substituted for OpenAI or Anthropic tokens. Run dates and baseline definitions must stay separate from future cloud results.',
      'Receipt/manifest verification demonstrates internal integrity relative to saved local receipts, not an independent attestation of the remote environment.'
    ]
    report={'schema':'gpu006-qwen90-read-only-audit-v1','plan_sha256':PLAN_SHA,'legacy_implementation_pins':PINS,
            'summary_receipt_expected_and_verified':SUMMARY_RECEIPT,'archived_summary':summary,
            'archive_inventory':sorted(inventory,key=lambda r:r['label']), 'archives_verified':len(inventory),
            'original_source_raw_verified':90, 'compiled_objects_raw_verified':len(compiled_rows),
            'raw_timing_comparisons_recomputed':len(raw_evidence),'raw_control_comparisons_recomputed':len(control_evidence),
            'summary_checkpoints_match':True,'frozen_selection_recomputed':True,
            'same_ptx_cubin_per_task_shape_across_conditions_trials':True,
            'all_failures_over_planned_slots':{'planned':90,'generation_failed':0,'correctness_failed':0,'measurement_invalid':0},
            'performance_vs_original':stats(r['speedup'] for r in original),
            'performance_vs_frozen_selected':stats(r['speedup'] for r in tuned),
            'speedups_gt_1_02_vs_original':fast,'invalid_controls':invalid_controls,
            'per_task':per_task,'per_condition':condition_stats,'paired_contrasts':contrast_stats,
            'generation_usage':generation_tokens,'execution_target':target,'limitations':limitations}
    if output_dir is not None:
        output=Path(os.path.abspath(output_dir))
        allowed=repo/'runs/gpu006-cloud180-v1'
        require(output.is_relative_to(allowed), 'Derived audit output must stay under new cloud180 directory')
        for name,data in [('audit.json',canonical(report)),('requests.csv',as_csv(request_audit)),('measurements.csv',as_csv(measurement_rows)),
                          ('speedups-gt-1.02.csv',as_csv(fast)),('compiled-identities.csv',as_csv(compiled_rows)),
                          ('paired-contrasts.csv',as_csv(pair_rows)),('raw-evidence.json',canonical(raw_evidence)),
                          ('control-evidence.json',canonical(control_evidence)),('REPORT.md',render_report(report).encode())]:
            write_derived(output/name,data)
    return report

def render_report(report):
    s=report['archived_summary']
    lines=[f"GPU006 Qwen90 L4 archive audit — real archived run completed {s['utc']} (22:42:57 JST on 2026-10-13).",
           '',f"Verified {report['archives_verified']} local checkpoint archives with the original byte-pinned validator. The summary is exactly 294977 bytes, 11 payload files; archive and manifest SHA-256 match the user-provided receipt. No archive was extracted.",
           '',f"All 90 fixed IDs preserve the plan model, task, information condition, trial, seed, prompt hash and original-source mapping. All 90 raw CUDA files equal their task original; all candidates passed the recorded strict bitwise and sanitizer checks. Raw PTX/cubin bytes matched same-target originals for all {report['compiled_objects_raw_verified']} saved compilation objects. All {report['raw_timing_comparisons_recomputed']} candidate and {report['raw_control_comparisons_recomputed']} control timing comparisons were recomputed from saved numeric rows with the original quality rule.",
           '', 'The study has 90 Qwen generation slots and 180 valid size comparisons for each baseline. The two invalid control cells are retained among 176 controls. Cloud 180 slots and A40 measurements remain pending.',
           '', '| Baseline | Comparisons | Geometric mean | Minimum | Maximum | >1.02 |', '|---|---:|---:|---:|---:|---:|']
    for label,key in [('Original source + original BLOCK','performance_vs_original'),('Original source + frozen selected BLOCK','performance_vs_frozen_selected')]:
        r=report[key]
        lines.append(f"| {label} | {r['n']} | {r['geometric_mean']:.12f} | {r['min']:.12f} | {r['max']:.12f} | {r['gt_1_02']} |")
    lines+=['','| Task | Qwen BLOCK (all 15 slots) | Original BLOCK | Selected BLOCK | GM vs original | GM vs selected |', '|---|---|---|---|---:|---:|']
    for r in report['per_task']:
        lines.append(f"| {r['task']} | {r['blocks'][0]} | {r['original_block']} | {r['frozen_selected_block']} | {r['original']['geometric_mean']:.12f} | {r['frozen_selected']['geometric_mean']:.12f} |")
    lines+=['','The exact 15 original-baseline speedup measurements are:', '', '| ID | Shape | BLOCK | Speedup |','|---|---|---|---:|']
    for r in report['speedups_gt_1_02_vs_original']:
        lines.append(f"| {r['id']} | {r['shape']} | {r['block']} | {r['speedup']:.15f} |")
    lines+=['', 'The two invalid controls and selection effects were verified from their own saved raw timing/identity rows:']
    for r in report['invalid_controls']:
        lines+=['',f"- {r['phase']} / {r['task']} / BLOCK {r['block']} / shape {r['shape']}: {', '.join(r['quality_reasons'])}. Candidate session medians: {r['session_medians']}; identity medians: {r['identity']['session_medians']}; identity reasons: {r['identity']['quality_reasons']}. {r['selection_impact']}. Evidence: `{r['raw_evidence']['archive']}:{r['raw_evidence']['timing_member']}` and `{r['raw_evidence']['identity_member']}`."]
    lines+=['', '| Contrast | Baseline | Valid matched cells | Equal-task GM ratio | Minimum cell ratio | Maximum cell ratio |', '|---|---|---:|---:|---:|---:|']
    for r in report['paired_contrasts']:
        lines.append(f"| {r['contrast']} | {r['baseline']} | {r['valid_pairs']}/{r['expected_pairs']} | {r['equal_task_geometric_mean']:.12f} | {r['cells']['min']:.12f} | {r['cells']['max']:.12f} |")
    lines+=['', 'A ratio above 1 favors the numerator condition. The CSV retains every task/trial/size/target/baseline match. These are descriptive quotients of separate baseline-normalized sessions; no condition-to-condition timing run or significance claim is implied.', '']
    lines += [x+'\n' for x in report['limitations']]
    lines+=['Derived files: audit.json (all summaries and archive pins), requests.csv (90-ID mapping), measurements.csv (360 candidate comparisons), speedups-gt-1.02.csv (15 exact cells), compiled-identities.csv (all compilation hashes), paired-contrasts.csv (all 288 matched cells), raw-evidence.json and control-evidence.json (archive/member/hash evidence).', '']
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    output=args.output_dir or args.repo_root/'runs/gpu006-cloud180-v1/qwen-audit'
    report=run_audit(args.repo_root,output)
    print(json.dumps({k:report[k] for k in ('archives_verified','original_source_raw_verified','compiled_objects_raw_verified','raw_timing_comparisons_recomputed','raw_control_comparisons_recomputed','performance_vs_original','performance_vs_frozen_selected')},indent=2))
    print('QWEN_AUDIT_REPORT='+str(output/'REPORT.md'))

if __name__=='__main__':
    main()