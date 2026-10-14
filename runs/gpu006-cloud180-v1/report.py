"""Within-model GPU006 condition analysis and actual provider usage reports.

Read-only old Qwen join. Derived report snapshots are content-addressed under the
new cloud run; no rankings, invented timings, inferred tokens or A40 results.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import decimal
import json
import math
from audit_qwen import CONTRASTS, PLAN_SHA, as_csv, load_legacy, run_audit, stats
from common import atomic_json, canonical, digest, parse, read, require, safe, write_once

PENDING_GENERATION = {'NOT_SUBMITTED','GENERATION_PENDING','SUBMISSION_UNKNOWN'}
PROVIDER_CONTRACT_STATUSES = {'model_mismatch','provider_contract_error','usage_schema_mismatch'}
INFRASTRUCTURE_STAGES = {'infrastructure_error','infrastructure_failed','environment_failed','resource_failed','validator_internal_error'}


def _index(items, allowed, name):
    require(isinstance(items,list),'Expected '+name+' list')
    ids=[r.get('id') for r in items if isinstance(r,dict)]
    require(len(ids)==len(items)==len(set(ids)) and set(ids)<=set(allowed),'Duplicate/foreign '+name+' IDs')
    return {r['id']:r for r in items}



def _artifact_bytes(run, reference, directory, label):
    require(isinstance(reference,dict) and isinstance(reference.get('path'),str),'Missing '+label+' artifact reference')
    relative=Path(reference['path'])
    require(not relative.is_absolute(),'Absolute '+label+' artifact path')
    path=safe(run/relative)
    require(path.is_relative_to(run/directory),'Escaping '+label+' artifact path')
    raw=read(path,256*1024**2)
    require(digest(raw)==reference.get('sha256'),'Changed '+label+' artifact')
    return raw


def _artifact(run, reference, directory, label):
    return parse(_artifact_bytes(run,reference,directory,label))


def _execution_evidence(run, ledger, by_plan):
    if ledger:
        require(digest(canonical(ledger.get('scope')))==ledger.get('scope_sha256'),'Report ledger fixed scope digest changed')
    batches=ledger.get('batches',{})
    require(isinstance(batches,dict),'Invalid report ledger batches')
    ledger_by_id={}
    records=[]
    for key,entry in batches.items():
        require(isinstance(entry,dict) and isinstance(entry.get('ids'),list),'Invalid ledger batch')
        ids=entry['ids']
        require(len(ids)==len(set(ids)),'Duplicate ledger batch IDs')
        for rid in ids:
            require(rid in by_plan and by_plan[rid]['provider']!='qwen','Foreign ledger ID')
            require(rid not in ledger_by_id,'Overlapping operational ledger IDs')
            require(entry['provider']==by_plan[rid]['provider'] and entry['trial']==by_plan[rid]['trial'],'Ledger batch identity differs')
            ledger_by_id[rid]={**entry,'key':key}
        records.append({field:entry.get(field) for field in ('provider','trial','ids','status','body_sha256','batch_id','submitted_at','collected_at')})
        records[-1]['key']=key
    manifest=None
    manifest_sha=None
    manifest_path=run/'execution-manifest.json'
    if manifest_path.exists():
        raw=read(manifest_path)
        manifest_sha=digest(raw)
        manifest=parse(raw)
        require(manifest.get('schema')=='gpu006-cloud180-execution-manifest-v2','Unexpected operational manifest schema')
        require(manifest.get('fixed_plan_sha256')==PLAN_SHA,'Operational manifest fixed plan changed')
        if 'fixed_scope' in manifest:
            require(digest(canonical(manifest['fixed_scope']))==manifest.get('fixed_scope_sha256'),'Operational manifest fixed scope digest changed')
        require(not ledger or manifest.get('fixed_scope_sha256')==ledger.get('scope_sha256'),'Operational manifest fixed scope changed')
        if ledger.get('execution_manifest_sha256') is not None:
            require(ledger['execution_manifest_sha256']==manifest_sha,'Ledger operational manifest digest changed')
        operational=manifest.get('operational_batches')
        require(isinstance(operational,list),'Missing operational batch partition')
        keys=[r.get('key') for r in operational if isinstance(r,dict)]
        require(len(keys)==len(operational)==len(set(keys)),'Duplicate operational batch keys')
        flat=[rid for item in operational for rid in item.get('ids',[])]
        cloud_ids={rid for rid,row in by_plan.items() if row['provider']!='qwen'}
        require(len(flat)==180 and len(set(flat))==180 and set(flat)==cloud_ids,'Operational manifest must partition the original 180 IDs')
        for item in operational:
            for rid in item['ids']:
                require(item['provider']==by_plan[rid]['provider'] and item['trial']==by_plan[rid]['trial'],'Operational manifest slot identity differs')
            if ledger:
                require(item['key'] in batches,'Operational manifest batch absent from ledger')
                entry=batches[item['key']]
                require(all(entry.get(field)==item.get(field) for field in ('ids','provider','trial','body_sha256')),'Operational manifest batch differs from ledger')
        if ledger:
            require(set(keys)==set(batches),'Operational manifest ledger batch coverage differs')
    proof=None
    reference=ledger.get('pilot_acceptance')
    if reference is not None:
        proof=_artifact(run,reference,'state/api-acceptance','API acceptance')
        require(proof.get('schema')=='gpu006-cloud180-pilot-acceptance-v2','Unexpected API acceptance proof schema')
        require(proof.get('actual_input_verified') is True,'API acceptance remote input is unverified')
        require(manifest_sha is not None and proof.get('execution_manifest_sha256')==manifest_sha,'API acceptance operational manifest digest changed')
        require(isinstance(proof.get('raw_response_artifacts'),list),'Missing API acceptance raw result artifacts')
        for artifact in [*proof['raw_response_artifacts'],proof.get('terminal_status_artifact')]:
            _artifact_bytes(run,artifact,'raw','API acceptance raw response')
        require(proof.get('status')==reference.get('status'),'API acceptance ledger status differs')
        rid=proof.get('custom_id')
        require(rid in by_plan and by_plan[rid]['provider']=='openai','API acceptance proof custom ID differs')
        entry=ledger_by_id.get(rid)
        require(entry and proof.get('batch_id')==entry.get('batch_id'),'API acceptance Batch ID differs')
        if proof.get('status')=='accepted':
            require(proof.get('accepted') is True and proof.get('returned_model')==by_plan[rid]['model'],'Accepted API proof model differs')
            require(all(setting.get('status')!='mismatch' for setting in proof.get('settings',{}).values()),'Accepted API proof contains setting mismatch')
        if manifest and manifest.get('mode')=='pilot_first_batch':
            pilot=manifest.get('pilot',{})
            require(rid==pilot.get('custom_id') and entry['key']==pilot.get('batch_key'),'API acceptance pilot differs')
            for field in ('request_body_sha256','submission_body_sha256'):
                require(proof.get(field)==pilot.get(field),'API acceptance submitted body digest differs')
    evidence={'fixed_plan_sha256':PLAN_SHA,'fixed_cloud_slots':180,
              'execution_manifest_sha256':manifest_sha,'execution_manifest':manifest,
              'operational_batches':sorted(records,key=lambda r:r['key']),
              'api_acceptance':{'current_account_request_status':proof.get('status') if proof else 'unverified',
                  'current_account_request_proof':proof,'proof_reference':reference,
                  'candidate_validation_is_acceptance_evidence':False,
                  'acceptance_proves_setting_influenced_content':False}}
    return ledger_by_id,evidence


def _local_collected(run, ledger, allowed):
    items=[]
    for entry in ledger.get('batches',{}).values():
        if entry.get('status')!='COLLECTED':
            continue
        batch_items=_artifact(run,{'path':entry.get('normalized_path'),'sha256':entry.get('normalized_sha256')},
                              'results/normalized','normalized provider result')
        batch_index=_index(batch_items,allowed,'normalized provider result')
        require(set(batch_index)==set(entry['ids']),'Normalized batch result ID coverage differs')
        items.extend(batch_items)
    _index(items,allowed,'partial collected provider result')
    final=run/'results/collected.json'
    if final.exists():
        final_items=parse(read(final))
        final_index=_index(final_items,allowed,'final collected provider result')
        require(len(final_index)==180,'Final collected result must retain all 180 original IDs')
        for item in items:
            require(final_index[item['id']]==item,'Final provider result differs from saved normalized batch')
        return final_items
    return items


def _provider_usage(provider, collected, outcomes, planned):
    rows=[]
    for rid in planned:
        item=collected.get(rid,outcomes.get(rid,{}))
        usage=item.get('raw_usage') if 'raw_usage' in item else item.get('usage')
        if usage is not None:
            require(isinstance(usage,dict),'Invalid usage object')
        rows.append({'id':rid,'usage':usage if usage else None,
                     'counter_source':'provider raw usage' if 'raw_usage' in item else 'normalized usage record'})
    fields=['input_tokens','output_tokens','total_tokens','cache_creation_input_tokens','cache_read_input_tokens','cached_input_tokens','reasoning_tokens']
    totals={}
    for field in fields:
        known=[]
        for row in rows:
            value=(row['usage'] or {}).get(field)
            if value is not None:
                require(type(value) is int and value>=0,'Invalid provider-native token counter')
                known.append(value)
        totals[field]={'known_sum':sum(known),'rows_with_counter':len(known),'rows_without_counter':len(rows)-len(known),
                       'complete_total':sum(known) if len(known)==len(rows) else None}
    nested={}
    for category in ('input_tokens_details','output_tokens_details','cache_creation'):
        keys=sorted({key for row in rows for key in (row['usage'] or {}).get(category,{})})
        for key in keys:
            values=[(row['usage'] or {}).get(category,{}).get(key) for row in rows]
            known=[x for x in values if x is not None]
            require(all(type(x) is int and x>=0 for x in known),'Invalid detailed provider usage counter')
            nested[category+'.'+key]={'known_sum':sum(known),'rows_with_counter':len(known),
                                     'rows_without_counter':len(rows)-len(known),
                                     'complete_total':sum(known) if len(known)==len(rows) else None}
    return {'provider':provider,'planned_slots':len(planned),'rows_with_any_reported_usage':sum(r['usage'] is not None for r in rows),
            'rows_without_reported_usage':sum(r['usage'] is None for r in rows),'token_counters':totals,
            'cache_and_reasoning_details':nested,'raw_usage_by_id':rows,'invoiced_cost_usd':None,
            'cost_status':'Provider invoice not present; missing counters remain unknown. No Qwen extrapolation or presumed cache discount.'}


def _matched_contrasts(provider, slots, measurements, plan):
    valid=[r for r in measurements if r['provider']==provider and r['measurement_valid']]
    lookup={(r['task'],r['trial'],r['shape'],r['baseline'],r['condition']):r for r in valid}
    pairs=[]
    summary=[]
    for contrast in CONTRASTS:
        left,right=contrast.split('/')
        for baseline in ('original','frozen_selected'):
            current=[]
            missing=[]
            for task in plan['tasks']:
                for trial in plan['trials']:
                    for shape in plan['performance_shapes'][task]:
                        shape_id='x'.join(map(str,shape))
                        a=lookup.get((task,trial,shape_id,baseline,left))
                        b=lookup.get((task,trial,shape_id,baseline,right))
                        if a and b:
                            r={'provider':provider,'model':a['model'],'contrast':contrast,'baseline':baseline,
                               'task':task,'trial':trial,'shape':shape_id,'execution_target':'L4',
                               'left_id':a['id'],'right_id':b['id'],'left_speedup':a['speedup'],'right_speedup':b['speedup'],
                               'normalized_speed_ratio':a['speedup']/b['speedup']}
                            pairs.append(r)
                            current.append(r)
                        else:
                            missing.append({'task':task,'trial':trial,'shape':shape_id,
                                            'left_valid':a is not None,'right_valid':b is not None})
            task_means=[{'task':t,**stats(r['normalized_speed_ratio'] for r in current if r['task']==t)} for t in plan['tasks']]
            eligible=[r['geometric_mean'] for r in task_means if r['n']==6]
            summary.append({'contrast':contrast,'baseline':baseline,'expected_matched_size_cells':36,
                            'valid_matched_size_cells':len(current),'missing_or_invalid_cells':missing,
                            'conditional_cell_stats':stats(r['normalized_speed_ratio'] for r in current),
                            'per_task':task_means,'tasks_with_all_six_pairs':len(eligible),
                            'equal_task_geometric_mean_on_fully_matched_tasks':stats(eligible)['geometric_mean'],
                            'ratio_above_one_favors':left,'direct_condition_to_condition_timing':False})
    return summary,pairs


def write_report(repo_root: Path, run_dir: Path, cloud_outcomes: list | None = None,
                 collected: list | None = None, quote: dict | None = None) -> dict:
    repo=safe(repo_root)
    run=safe(run_dir)
    require(run.is_relative_to(repo/'runs/gpu006-cloud180-v1'),'Analysis writes must stay under the new cloud180 run')
    raw_plan=read(repo/'runs/gpu006-target-info-v1/inputs/plan.json')
    require(digest(raw_plan)==PLAN_SHA,'Fixed analysis plan changed')
    plan=parse(raw_plan)
    by_plan={r['id']:r for r in plan['requests']}
    require(len(by_plan)==270,'Analysis must retain all 270 planned IDs')
    qwen_audit=run_audit(repo)
    legacy=load_legacy(repo)
    old=repo/'runs/gpu006-qwen-experiment-v1/results/l4'
    def old_archive(label):
        return legacy.G.read_archive(read(old/(label+'.tar.gz'),256*1024**2),parse(read(old/(label+'-receipt.json'))))
    qwen_files=old_archive('summary')
    qwen_outcomes=parse(qwen_files['outcomes.json'])
    qwen_generation_times={}
    for group in legacy.qwen_groups(plan):
        files=old_archive('generated-'+group['label'])
        for rid in group['request_ids']:
            condition=by_plan[rid]['information_condition']
            qwen_generation_times[rid]=parse(files[condition+'/intent.json'])['utc']
    cloud_meta={}
    source_kind='No cloud worker outcomes present'
    cloud_archive=run/'results/l4/summary.tar.gz'
    if cloud_archive.exists():
        receipt=parse(read(run/'results/l4/summary-receipt.json'))
        files=legacy.G.read_archive(read(cloud_archive,256*1024**2),receipt)
        require(files['plan.json']==raw_plan,'Cloud worker archived plan differs')
        verified_outcomes=parse(files['outcomes.json'])
        require(len(verified_outcomes)==180,'Cloud final archive must retain 180 outcomes')
        if cloud_outcomes is not None:
            require(cloud_outcomes==verified_outcomes,'Supplied cloud outcomes differ from verified worker archive')
        cloud_outcomes=verified_outcomes
        cloud_meta=parse(files['summary.json'])
        require(cloud_meta['plan_sha256']==PLAN_SHA and cloud_meta['cloud_slots']==180,'Wrong cloud worker scope')
        source_kind='Verified cloud worker summary archive '+receipt['sha256']
    elif cloud_outcomes is not None:
        source_kind='Supplied worker outcomes; final local archive absent (not independently archive-verified here)'
    cloud_ids={rid for rid,r in by_plan.items() if r['provider']!='qwen'}
    cloud_by_id=_index(cloud_outcomes or [],cloud_ids,'cloud worker outcome')
    qwen_by_id=_index(qwen_outcomes,{rid for rid,r in by_plan.items() if r['provider']=='qwen'},'Qwen outcome')
    ledger={}
    ledger_path=run/'state/ledger.json'
    if ledger_path.exists():
        ledger=parse(read(ledger_path))
        require(ledger['scope']['plan_sha256']==PLAN_SHA,'Report ledger plan scope differs')
    ledger_by_id,execution_evidence=_execution_evidence(run,ledger,by_plan)
    compatibility=(quote or {}).get('api_compatibility_evidence',{})
    acceptance=execution_evidence['api_acceptance']
    public=compatibility.get('public_documentation')
    if public is None and (run/'official-api-evidence.json').exists():
        raw=read(run/'official-api-evidence.json')
        document=parse(raw)
        require(document.get('schema')=='gpu006-official-api-evidence-v1','Unexpected public API evidence schema')
        support=document.get('public_parameter_support',{})
        public={'status':'unsupported' if 'unsupported' in support.values() else 'documented' if document.get('parameters_verified') is True else 'unverified',
                'provider_support':support,'parameters_verified':document.get('parameters_verified'),
                'explicitly_unsupported_parameters':document.get('explicitly_unsupported_parameters'),
                'verified_at':document.get('verified_at'),'evidence_path':'official-api-evidence.json','evidence_sha256':digest(raw)}
    acceptance['public_documentation']=public or {'status':'not_verified','provider_support':None,'parameters_verified':None}
    acceptance['historical_exact_setting_acceptance']=compatibility.get('historical_exact_setting_acceptance',{'status':'not_verified','records':[]})
    acceptance['quote_current_account_request_acceptance']=compatibility.get('current_account_request_acceptance',{'status':'not_yet_tested','pilot_custom_id':(execution_evidence['execution_manifest'] or {}).get('pilot',{}).get('custom_id')})
    if collected is None:
        collected=_local_collected(run,ledger,cloud_ids)
    collected_by_id=_index(collected or [],cloud_ids,'collected provider result')
    slots=[]
    measurements=[]
    compilation_identities=[]
    for row in plan['requests']:
        provider=row['provider']
        rid=row['id']
        outcome=qwen_by_id.get(rid) if provider=='qwen' else cloud_by_id.get(rid)
        result=collected_by_id.get(rid,{})
        entry=ledger_by_id.get(rid,{})
        if result.get('requested_model') is not None:
            require(result['requested_model']==row['model'],'Collected requested model differs: '+rid)
        generation_status=outcome.get('generation_status') if outcome else result.get('generation_status')
        if generation_status is None:
            generation_status=('SUBMISSION_UNKNOWN' if entry.get('status') in ('SUBMISSION_UNKNOWN','SUBMISSION_INTENT') else
                               'GENERATION_PENDING' if entry.get('batch_id') else 'NOT_SUBMITTED')
        if outcome and result.get('generation_status') is not None:
            require(outcome.get('generation_status')==result['generation_status'] or
                    (result['generation_status']=='saved' and outcome.get('generation_status')=='invalid_generation'),
                    'Worker and provider generation status differ: '+rid)
        if outcome:
            for key in ('provider','model','task','trial','messages_sha256','original_source_sha256'):
                require(outcome[key]==row[key],'Worker outcome identity differs: '+rid+' '+key)
            require(outcome['condition']==row['information_condition'],'Worker condition differs')
        stage=outcome.get('stage') if outcome else ('EVALUATION_PENDING' if generation_status=='saved' else generation_status)
        infra=stage in INFRASTRUCTURE_STAGES
        terminal=bool(outcome and not infra and stage not in ('NOT_STARTED','EVALUATION_PENDING'))
        correctness=outcome.get('correctness_passed') if outcome else None
        slot={'id':rid,'provider':provider,'model':row['model'],'task':row['task'],'condition':row['information_condition'],
              'trial':row['trial'],'generation_status':generation_status,'evaluation_stage':stage,
              'processing_terminal':terminal,'correctness_passed':correctness,'infrastructure_anomaly':infra,
              'generation_failed':generation_status not in PENDING_GENERATION|{'saved'}|PROVIDER_CONTRACT_STATUSES,
              'provider_contract_failure':generation_status in PROVIDER_CONTRACT_STATUSES,
              'validation_failed':bool(outcome and generation_status=='saved' and correctness is False and not infra),
              'measurement_invalid':False,'valid_original_size_comparisons':0,'valid_selected_size_comparisons':0,
              'all_l4_checks_and_comparisons_valid':False,
              'generation_backend':'llama.cpp native /completion' if provider=='qwen' else provider+' Batch API /v1/responses' if provider=='openai' else 'Anthropic Message Batches API',
              'generation_requested_at':qwen_generation_times.get(rid),
              'submitted_at':entry.get('submitted_at'),'collected_at':entry.get('collected_at'),
              'operational_batch_key':entry.get('key'),'operational_batch_status':entry.get('status'),'batch_id':entry.get('batch_id'),
              'submission_body_sha256':entry.get('body_sha256'),
              'provider_response_id':result.get('provider_response_id',outcome.get('provider_response_id') if outcome else None),
              'api_request_acceptance_status':execution_evidence['api_acceptance']['current_account_request_status'] if rid==(execution_evidence['api_acceptance']['current_account_request_proof'] or {}).get('custom_id') else None,
              'execution_completed_at':qwen_audit['archived_summary']['utc'] if provider=='qwen' else cloud_meta.get('utc'),
              'execution_target':'L4' if outcome else None,'gpu_uuid':qwen_audit['archived_summary']['gpu_uuid'] if provider=='qwen' else cloud_meta.get('gpu_uuid'),
              'source_sha256':outcome.get('source_sha256') if outcome else None,
              'source_equals_original':outcome.get('source_equals_original') if outcome else None,
              'block':outcome.get('block') if outcome else None,'error':outcome.get('error') if outcome else result.get('error'),
              'A40':None,'evidence': 'Immutable verified Qwen90 archive' if provider=='qwen' else source_kind}
        if outcome:
            for shape_name,compilation in outcome.get('compilation',{}).items():
                compilation_identities.append({'id':rid,'provider':provider,'model':row['model'],'task':row['task'],
                    'condition':row['information_condition'],'trial':row['trial'],'shape':shape_name,
                    'compile_ok':compilation.get('ok'),'ptx_sha256':compilation.get('ptx_sha256'),
                    'cubin_sha256':compilation.get('cubin_sha256'),'options':compilation.get('compile',{}).get('options'),
                    'record_kind':'Actual raw bytes verified by Qwen audit' if provider=='qwen' else 'Saved worker compilation record'})
            for kind,baseline in (('measurements','original'),('tuned_measurements','frozen_selected')):
                metrics=outcome.get(kind,[])
                require(isinstance(metrics,list),'Invalid worker measurement list')
                require(len({tuple(m['shape']) for m in metrics})==len(metrics),'Duplicate worker measurement shape')
                if correctness is True:
                    require({tuple(m['shape']) for m in metrics}=={tuple(s) for s in plan['performance_shapes'][row['task']]},'Successful candidate measurement shape coverage differs')
                for metric in metrics:
                    shape='x'.join(map(str,metric['shape']))
                    valid=metric.get('measurement_valid') is True
                    value=metric.get('speedup')
                    if valid:
                        require(type(value) in (int,float) and value>0 and math.isfinite(value),'Invalid measured speed ratio')
                        slot['valid_original_size_comparisons' if baseline=='original' else 'valid_selected_size_comparisons']+=1
                    else:
                        slot['measurement_invalid']=True
                    measurements.append({'id':rid,'provider':provider,'model':row['model'],'task':row['task'],'condition':row['information_condition'],
                                         'trial':row['trial'],'shape':shape,'execution_target':'L4','baseline':baseline,
                                         'measurement_valid':valid,'speedup':value,'quality_reasons':metric.get('quality_reasons',[]),
                                         'block':outcome.get('block'),'reference_block':metric.get('reference_block',legacy.C.SPECS[row['task']]['base']) if baseline=='original' else metric.get('reference_block'),
                                         'same_ptx_as_original':metric.get('same_ptx'),'same_cubin_as_original':metric.get('same_cubin'),
                                         'same_launch_as_original':outcome.get('block')==legacy.C.SPECS[row['task']]['base'],
                                         'run_completed_at':slot['execution_completed_at'],'gpu_uuid':slot['gpu_uuid'],'A40_speedup':None})
        slot['all_l4_checks_and_comparisons_valid']=bool(correctness is True and slot['valid_original_size_comparisons']==2 and slot['valid_selected_size_comparisons']==2)
        slots.append(slot)
    models=[]
    all_pairs=[]
    for provider in ('qwen','openai','anthropic'):
        ss=[r for r in slots if r['provider']==provider]
        mm=[r for r in measurements if r['provider']==provider and r['measurement_valid']]
        contrasts,pairs=_matched_contrasts(provider,ss,measurements,plan)
        all_pairs.extend(pairs)
        conditions=[]
        for condition in plan['information_conditions']:
            subset=[r for r in ss if r['condition']==condition]
            conditions.append({'condition':condition,'planned_slots':len(subset),'terminal_slots':sum(r['processing_terminal'] for r in subset),
                               'generation_failures':sum(r['generation_failed'] for r in subset),'validation_failures':sum(r['validation_failed'] for r in subset),
                               'measurement_invalid_slots':sum(r['measurement_invalid'] for r in subset),
                               'provider_contract_failures':sum(r['provider_contract_failure'] for r in subset),
                               'conditional_performance':{baseline:stats(r['speedup'] for r in mm if r['condition']==condition and r['baseline']==baseline) for baseline in ('original','frozen_selected')}})
        models.append({'provider':provider,'model':plan['generation_settings'][provider]['id'],'planned_slots':90,
                       'processing_terminal_slots':sum(r['processing_terminal'] for r in ss),'pending_processing_slots':sum(not r['processing_terminal'] for r in ss),
                       'generation_status_counts':dict(Counter(r['generation_status'] for r in ss)),
                       'generation_failures_over_90':sum(r['generation_failed'] for r in ss),
                       'provider_contract_failures_over_90':sum(r['provider_contract_failure'] for r in ss),'validation_failures_over_90':sum(r['validation_failed'] for r in ss),
                       'measurement_invalid_slots_over_90':sum(r['measurement_invalid'] for r in ss),
                       'infrastructure_anomaly_slots':sum(r['infrastructure_anomaly'] for r in ss),
                       'all_l4_checks_and_comparisons_valid_over_90':sum(r['all_l4_checks_and_comparisons_valid'] for r in ss),
                       'observed_failure_rate_over_planned_slots':sum(r['generation_failed'] or r['provider_contract_failure'] or r['validation_failed'] or r['measurement_invalid'] for r in ss)/90,
                       'pending_is_counted_as_failure':False,
                       'source_and_launch_identity':{'observed_source_slots':sum(r['source_sha256'] is not None for r in ss),
                            'source_equals_original_slots':sum(r['source_equals_original'] is True for r in ss),
                            'per_task':[{'task':task,'observed_source_hashes':sorted({r['source_sha256'] for r in ss if r['task']==task and r['source_sha256'] is not None}),
                                'observed_blocks':[list(b) for b in sorted({tuple(r['block']) for r in ss if r['task']==task and r['block'] is not None})],
                                'original_block':legacy.C.SPECS[task]['base']} for task in plan['tasks']]},
                       'conditional_performance_on_valid_size_cells':{baseline:stats(r['speedup'] for r in mm if r['baseline']==baseline) for baseline in ('original','frozen_selected')},
                       'per_condition':conditions,'primary_within_model_contrasts':contrasts})
    usage=[_provider_usage(p,collected_by_id,cloud_by_id,[rid for rid,r in by_plan.items() if r['provider']==p]) for p in ('openai','anthropic')]
    total_terminal=sum(r['processing_terminal'] for r in slots)
    total_valid=sum(r['all_l4_checks_and_comparisons_valid'] for r in slots)
    report={'schema':'gpu006-within-model-analysis-v1','plan_sha256':PLAN_SHA,'planned_slots':270,
            'processing_terminal_slots':total_terminal,'pending_processing_slots':270-total_terminal,
            'all_270_slots_processed':total_terminal==270,'successful_l4_candidate_slots':total_valid,
            'all_270_candidates_successful':total_valid==270,'A40_evaluation_complete':False,'A40_columns':None,
            'model_ranking_performed':False,'models':models,'provider_usage':usage,
            'qwen_native_usage':qwen_audit['generation_usage'],'qwen_audit_summary_receipt':qwen_audit['summary_receipt_expected_and_verified'],
            'cloud_worker_evidence':source_kind,'cloud_worker_summary':cloud_meta or None,
            'execution_provenance':execution_evidence,
            'quote':quote,'paid_budget_inferred_from_proposed_ten_usd':False,
            'cost_totals':{'actual_invoiced_usd':None,'quoted_reserved_usd':quote.get('reserved_usd') if quote else None},
            'limitations':qwen_audit['limitations']+[
                'Failure rates retain all 90 planned slots for each model and distinguish pending slots. Conditional performance excludes invalid or unavailable timing cells and reports the number used.',
                'Generation-request timestamps, submitted/collected timestamps, run-completion timestamps and backend are separate fields; missing exact generation/execution times remain null.',
                'The one-request GPT acceptance pilot is an operational split of one original planned ID, not an additional experimental slot. Per-request acceptance remains separate from candidate-format, numeric and timing outcomes; absent parameter echoes remain unknown and acceptance does not prove that a setting influenced content.',
                'Final report snapshots are derived analysis. Supplied outcomes without their local worker summary archive are labeled as lacking independent archive verification.'
            ]}
    snapshot_id=digest(canonical(report))
    destination=run/'analysis/snapshots'/snapshot_id
    write_once(destination/'report.json',canonical(report))
    write_once(destination/'slots.csv',as_csv(slots))
    write_once(destination/'measurements.csv',as_csv(measurements))
    write_once(destination/'paired-contrasts.csv',as_csv(all_pairs))
    write_once(destination/'compiled-identities.csv',as_csv(compilation_identities))
    write_once(destination/'REPORT.md',render_report(report).encode())
    atomic_json(run/'analysis/latest.json',{'snapshot_sha256':snapshot_id,'report_path':str((destination/'report.json').relative_to(run)),
                                         'markdown_path':str((destination/'REPORT.md').relative_to(run)),
                                         'processing_terminal_slots':total_terminal,'successful_l4_candidate_slots':total_valid})
    return report


def render_report(report):
    lines=[f"GPU006 information-condition analysis: {report['processing_terminal_slots']}/270 planned slots have terminal processing records; {report['successful_l4_candidate_slots']}/270 candidates have all L4 validation and comparison cells valid.",
           '',f"All 270 processed: {report['all_270_slots_processed']}. All 270 successful: {report['all_270_candidates_successful']}. A40 candidate measurements: unavailable.",
           '', '| Model | Planned | Terminal | Pending | Generation failures | Provider contract failures | Validation failures | Timing-invalid slots | Fully valid L4 candidates |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in report['models']:
        lines.append(f"| {m['model']} | 90 | {m['processing_terminal_slots']} | {m['pending_processing_slots']} | {m['generation_failures_over_90']} | {m['provider_contract_failures_over_90']} | {m['validation_failures_over_90']} | {m['measurement_invalid_slots_over_90']} | {m['all_l4_checks_and_comparisons_valid_over_90']} |")
    acceptance=report['execution_provenance']['api_acceptance']
    manifest=report['execution_provenance']['execution_manifest']
    lines+=['', 'Current-account fixed-setting GPT request acceptance: '+acceptance['current_account_request_status']+'. Candidate format, numeric validation and timing do not determine API acceptance. Acceptance supplies no proof that each setting influenced content.',
            'Public documentation: '+str(acceptance['public_documentation'].get('status','not_verified'))+'. Historical exact-setting acceptance: '+str(acceptance['historical_exact_setting_acceptance'].get('status','not_verified'))+'. These evidence states do not establish current-account request acceptance.',
            'Operational submission partition: '+(manifest.get('mode','unknown') if manifest else 'No execution manifest present')+'. All original 180 cloud IDs remain in scope; the pilot is counted once.']
    lines+=['', 'Performance below is conditional on valid size comparison cells. Pending requests are retained separately from failures. The report preserves within-model comparisons and performs no model ranking.',
            '', '| Model | Baseline | Valid size cells | GM speedup | Minimum | Maximum |', '|---|---|---:|---:|---:|---:|']
    for m in report['models']:
        for baseline,r in m['conditional_performance_on_valid_size_cells'].items():
            values=['unknown' if r[k] is None else f"{r[k]:.12f}" for k in ('geometric_mean','min','max')]
            lines.append(f"| {m['model']} | {baseline} | {r['n']}/180 | {' | '.join(values)} |")
    lines+=['', '| Model | Contrast | Baseline | Matched valid cells | Fully matched tasks | Equal-task GM ratio |', '|---|---|---|---:|---:|---:|']
    for m in report['models']:
        for c in m['primary_within_model_contrasts']:
            value=c['equal_task_geometric_mean_on_fully_matched_tasks']
            lines.append(f"| {m['model']} | {c['contrast']} | {c['baseline']} | {c['valid_matched_size_cells']}/36 | {c['tasks_with_all_six_pairs']}/6 | {'unknown' if value is None else format(value,'.12f')} |")
    lines+=['', 'Condition ratios divide separate baseline-normalized sessions, preserving model, task, trial, size, target and baseline. A value above 1 favors the numerator condition. Missing pairs remain explicit. The 1.02 threshold is descriptive and supplies no significance or equivalence claim.',
            '', 'Actual provider usage retains raw per-ID counters, including cached-input and reasoning details when supplied. Missing usage is unknown; Qwen native counts are kept separately. Actual invoiced USD remains unknown without provider invoice evidence.', '']
    for item in report['provider_usage']:
        lines.append(f"{item['provider']}: {item['rows_with_any_reported_usage']}/90 rows have provider usage counters; {item['rows_without_reported_usage']}/90 do not. Known input sum {item['token_counters']['input_tokens']['known_sum']}; known output sum {item['token_counters']['output_tokens']['known_sum']}; complete totals remain {'available' if item['token_counters']['input_tokens']['complete_total'] is not None and item['token_counters']['output_tokens']['complete_total'] is not None else 'unknown'}.")
        lines.append('')
    lines += [x+'\n' for x in report['limitations']]
    return '\n'.join(lines)