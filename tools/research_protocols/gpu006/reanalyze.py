#!/usr/bin/env python3
"""Offline GPU006 reanalysis of public CSV/JSON and CUDA bytes; stdlib only."""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/"research-artifacts/gpu006"
def data(name):return json.loads((ROOT/name).read_text())
def rows(name):
    with (ROOT/name).open(newline='') as f:return list(csv.DictReader(f))
def truth(value):return str(value).lower()=='true'
def geometric_mean(values):
    xs=list(values)
    return math.exp(sum(math.log(v) for v in xs)/len(xs)) if xs else None

def check():
    slots=rows('slots.csv');measurements=rows('measurements.csv');report=data('report.json');candidates=data('candidates.json');protocol=data('protocol.json')
    assert len(slots)==len({r['id'] for r in slots})==270
    assert collections.Counter(r['provider'] for r in slots)=={'qwen':90,'openai':90,'anthropic':90}
    assert collections.Counter(r['generation_status'] for r in slots)=={'saved':255,'invalid_generation':15}
    assert all(truth(r['processing_terminal']) and r['A40']=='not_measured' for r in slots)
    assert len(candidates)==len({r['id'] for r in candidates})==255
    byid={r['id']:r for r in slots}
    for item in candidates:
        source=(ROOT/'candidates'/(item['id']+'.cu')).read_bytes()
        assert hashlib.sha256(source).hexdigest()==item['source_sha256']==byid[item['id']]['source_sha256']
        assert item['block'] in protocol['allowed_blocks'][item['task']]
    prompts=[json.loads(line) for line in (ROOT/'prompts.jsonl').read_text().splitlines()]
    assert len(prompts)==270 and {r['id'] for r in prompts}==set(byid)
    for row in prompts:
        encoded=(json.dumps(row['messages'],ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
        assert hashlib.sha256(encoded).hexdigest()==row['messages_sha256']
        original=(ROOT/'reference/sources'/(row['task']+'.cu')).read_bytes()
        assert hashlib.sha256(original).hexdigest()==row['original_source_sha256']
    assert len(measurements)==1020 and sum(truth(r['measurement_valid']) for r in measurements)==1018
    assert all(not r['A40_speedup'] for r in measurements)
    successful=sum(truth(r['all_l4_checks_and_comparisons_valid']) for r in slots)
    assert successful==report['successful_l4_candidate_slots']==253
    means={}
    for model in report['models']:
        for baseline in ('original','frozen_selected'):
            values=[float(r['speedup']) for r in measurements if r['provider']==model['provider'] and r['baseline']==baseline and truth(r['measurement_valid'])]
            expected=model['conditional_performance_on_valid_size_cells'][baseline]
            assert len(values)==expected['n']
            actual=geometric_mean(values)
            assert math.isclose(actual,expected['geometric_mean'],rel_tol=1e-12)
            means[model['provider']+'/'+baseline]={'n':len(values),'geometric_mean':actual}
    pairs=rows('paired-contrasts.csv')
    assert len(pairs)==800
    measured={(r['id'],r['baseline'],r['shape']):r for r in measurements}
    for row in pairs:
        left=measured[(row['left_id'],row['baseline'],row['shape'])]
        right=measured[(row['right_id'],row['baseline'],row['shape'])]
        assert truth(left['measurement_valid']) and truth(right['measurement_valid'])
        assert math.isclose(float(row['left_speedup']),float(left['speedup']),rel_tol=1e-12)
        assert math.isclose(float(row['right_speedup']),float(right['speedup']),rel_tol=1e-12)
        assert math.isclose(float(row['normalized_speed_ratio']),float(left['speedup'])/float(right['speedup']),rel_tol=1e-12)
    contrasts={}
    for model in report['models']:
        for summary in model['primary_within_model_contrasts']:
            selected=[r for r in pairs if r['provider']==model['provider'] and r['contrast']==summary['contrast'] and r['baseline']==summary['baseline']]
            values=[float(r['normalized_speed_ratio']) for r in selected]
            expected=summary['conditional_cell_stats']
            assert len(values)==expected['n']==summary['valid_matched_size_cells']
            assert math.isclose(geometric_mean(values),expected['geometric_mean'],rel_tol=1e-12)
            assert sum(v>1.02 for v in values)==expected['gt_1_02']
            assert math.isclose(min(values),expected['min'],rel_tol=1e-12)
            assert math.isclose(max(values),expected['max'],rel_tol=1e-12)
            complete=[]
            for task in summary['per_task']:
                subset=[float(r['normalized_speed_ratio']) for r in selected if r['task']==task['task']]
                assert len(subset)==task['n']
                if subset:assert math.isclose(geometric_mean(subset),task['geometric_mean'],rel_tol=1e-12)
                else:assert task['geometric_mean'] is None
                if len(subset)==6:complete.append(geometric_mean(subset))
            assert len(complete)==summary['tasks_with_all_six_pairs']
            equal_task=geometric_mean(complete)
            if equal_task is None:assert summary['equal_task_geometric_mean_on_fully_matched_tasks'] is None
            else:assert math.isclose(equal_task,summary['equal_task_geometric_mean_on_fully_matched_tasks'],rel_tol=1e-12)
            contrasts[model['provider']+'/'+summary['contrast']+'/'+summary['baseline']]={'n':len(values),'geometric_mean':geometric_mean(values),'fully_matched_tasks':len(complete),'equal_task_geometric_mean':equal_task}
    assert len(contrasts)==24
    return {'planned_slots':270,'saved_candidates':255,'invalid_generation':15,'all_l4_quality_valid_candidates':253,'measurement_cells':1020,'valid_measurement_cells':1018,'A40':'not_measured','means':means,'paired_contrast_cells':len(pairs),'within_model_contrasts':contrasts,'server_connections':0,'API_calls':0,'compilations':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true',required=True);parser.parse_args()
    print(json.dumps(check(),sort_keys=True,indent=2))
