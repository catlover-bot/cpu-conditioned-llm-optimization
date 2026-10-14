# Public fixture scope only. This never authenticates or reconstructs a live L4.
from pathlib import Path
from collections import Counter
from common import REPO,PLAN_SHA,INPUT,read,parse,require,digest,canonical
from providers import draft_rows,validate_request

def validate_inputs(repo_root=REPO):
    repo=Path(repo_root);raw=read(repo/INPUT/'inputs/plan.json');require(digest(raw)==PLAN_SHA,'Immutable plan differs')
    plan=parse(raw);rows=plan['requests'];require(Counter(r['provider'] for r in rows)=={'qwen':90,'openai':90,'anthropic':90},'Fixed270 coverage differs')
    batches=[]
    for trial in (1,2,3):
        for provider in ('openai','anthropic'):
            suffix='jsonl' if provider=='openai' else 'json'
            payload=read(repo/INPUT/f'inputs/drafts/trial-{trial:02d}/{provider}-requests-NOT-SUBMITTED.{suffix}')
            requests=draft_rows(provider,payload);selected=[r for r in rows if r['provider']==provider and r['trial']==trial]
            require(len(requests)==len(selected)==30,'Exact trial coverage differs')
            for request,row in zip(requests,selected):
                body=validate_request(provider,request)
                messages=body['input'] if provider=='openai' else [{'role':'system','content':body['system']}]+body['messages']
                require(request['custom_id']==row['id'] and messages==row['messages'],'Fixture request differs from actual prompt')
            batches.append({'key':f'{provider}-trial-{trial:02d}','provider':provider,'trial':trial,'ids':[r['id'] for r in selected],'payload':payload,'requests':requests,'body_sha256':digest(payload)})
    target={'publication_fixture_only':True,'host':'example.invalid','port':22,'hardware':'NVIDIA L4','retired':True}
    scope={'schema':'gpu006-cloud180-scope-v1','plan_sha256':PLAN_SHA,'trials':[1,2,3],'requests':180,'per_request_max_output_tokens':8192,'models':{p:plan['generation_settings'][p]['id'] for p in ('openai','anthropic')},'ids':[r['id'] for r in rows if r['provider']!='qwen'],'batches':[{k:b[k] for k in ('key','provider','trial','ids','body_sha256')} for b in batches],'target_sha256':digest(canonical(target)),'automatic_retry':False}
    return {'plan':plan,'batches':batches,'scope':scope,'scope_sha256':digest(canonical(scope)),'target':target}
