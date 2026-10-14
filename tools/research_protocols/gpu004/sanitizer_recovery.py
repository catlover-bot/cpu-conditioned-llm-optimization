#!/usr/bin/env python3
"""GPU004B: budget-gated Batch API generation and the unchanged GPU002 CUDA evaluator.

First balanced tranche only: 6 tasks x 5 arms x 1 trial x 3 providers = 90 slots.
OpenAI/Anthropic: 30 requests each, exactly one batch creation per provider.
Qwen: 30 local generations. Prior 270-slot plan is NOT declared complete.
No synchronous paid generation, automatic resubmission, fallback, or Pod deletion.
"""
from __future__ import annotations

# PUBLIC ARCHIVAL COPY. Source hashes are recorded in publication-provenance.json.
# Only operational instance fields and dependency loading differ from the source.
# Offline analysis needs no allocation, provider account, CUDA build or GPU.
import importlib.util as _public_importlib
from pathlib import Path as _PublicPath
_public_path = _PublicPath(__file__).resolve().parent.parent / 'gpu004' / '_public.py'
_public_spec = _public_importlib.spec_from_file_location('_cpucond_public_dependencies', _public_path)
_public = _public_importlib.module_from_spec(_public_spec)
_public_spec.loader.exec_module(_public)
import argparse, base64, contextlib, copy, decimal, getpass, gzip, hashlib
import http.client, io, json, math, os, re, signal, ssl, sys, time, traceback
import types, unittest, uuid
from pathlib import Path
from collections import Counter
from unittest import mock

BASE_SHA = '4fd39dc0424b59d1fd2303ee018600a249da8111f9ac9f67ec1958cf3f21a76f'
BASE_EMBED = _public.encoded_module('multimodel.py')

def digest(raw): return hashlib.sha256(raw).hexdigest()
BASE_RAW = gzip.decompress(base64.b64decode(BASE_EMBED, validate=True))
if digest(BASE_RAW) != BASE_SHA: raise RuntimeError('Pinned GPU004 dependency differs')
M = _public.load_module('multimodel.py', BASE_SHA)


C, P = M.C, M.P
need, require, canon, parse, read, save, jw, hfile, now = M.need, M.require, M.canon, M.parse, M.read, M.save, M.jw, M.hfile, M.now
Blocked, NumericFailure = M.Blocked, M.NumericFailure
D = decimal.Decimal
VERSION = 'gpu004b-batch-first-balanced-trial-v1'
ROOT = Path('/workspace/gpu004-batch-budget-v1')
LOCAL_REL = Path('workspace/cpu-conditioned-llm-optimization/runs/gpu004-batch-budget-v1')
CLOUD = ('openai', 'anthropic')
HOSTS = {'openai':'api.openai.com', 'anthropic':'api.anthropic.com'}
BATCH_PRICES = {'openai':('1','6'), 'anthropic':('1.50','7.50')}
PRICE_REFS = {
 'openai':'https://developers.openai.com/api/docs/pricing',
 'anthropic':'https://platform.claude.com/docs/en/about-claude/pricing',
 'batch_openai':'https://developers.openai.com/api/docs/guides/batch',
 'batch_anthropic':'https://platform.claude.com/docs/en/build-with-claude/batch-processing'}
PRICE_DATE = '2026-10-09'
RUN_SECONDS, ACK_SECONDS = 72*3600, 36*3600
BATCH_POLL_SECONDS = 60
_ORIGINAL_PAYLOAD = M.api_payload
_ORIGINAL_GENERATE = M.generate_group
_ORIGINAL_PLAN = M.make_plan


def configure(root=None):
    global ROOT
    if root is not None: ROOT = Path(root)
    M.__file__ = __file__; M.LOCAL_REL = LOCAL_REL; M.VERSION = VERSION
    M.REPEATS = (1,); M.TOTAL = 90
    M.RUN_SECONDS, M.ACK_SECONDS = RUN_SECONDS, ACK_SECONDS
    M.PRICE_DATE, M.PRICE_REFS = PRICE_DATE, PRICE_REFS
    for p, (a,b) in BATCH_PRICES.items():
        M.PRESETS[p]['input_usd_per_million'] = a
        M.PRESETS[p]['output_usd_per_million'] = b
    M.configure(ROOT)
    P.PORT = 11648
configure()


def cfg_document():
    return {'schema':VERSION, 'models':copy.deepcopy(M.PRESETS),
            'model_provenance':'explicit_new_gpu_cohort_ids'}


def api_payload(provider, r, cfg):
    body = _ORIGINAL_PAYLOAD(provider, r, cfg)
    # Batch selects the asynchronous price tier; do not ask for synchronous default/Fast.
    body.pop('service_tier', None)
    return body
M.api_payload = api_payload


def make_plan(cfg, env):
    plan = _ORIGINAL_PLAN(cfg,env)
    # Use the A40 for Qwen while the provider-owned cloud batches run.
    # This execution order is frozen before generation, not chosen using results.
    plan['groups'] = [g for g in plan['groups'] if g['provider']=='qwen'] + [g for g in plan['groups'] if g['provider']!='qwen']
    plan.update(cloud_transport='provider_batch_apis_only', planned_cloud_requests=60,
        selected_trial_numbers=[1], deferred_trial_numbers=[2,3], prior_270_plan_complete=False,
        changed_scope='Batch transport and first balanced trial only; prompt, model generation caps and CUDA core retained',
        execution_order='Qwen groups first during cloud batch processing; within-group arm order frozen',
        no_automatic_next_tranche=True)
    M.validate_plan(plan)
    return plan
M.make_plan = make_plan


def money(value):
    try: out = D(str(value))
    except decimal.InvalidOperation as e: raise Blocked('Invalid dollar limit') from e
    need(out.is_finite() and D(0)<out<=D(100), 'Dollar limit must be finite, positive, and at most 100')
    return out


class Secrets:
    def __init__(self, use_env=False):
        self.values = {}
        # Never pass API keys on to SSH children. Default: re-enter, avoiding stale env keys.
        for p,var in [('openai','OPENAI_API_KEY'),('anthropic','ANTHROPIC_API_KEY')]:
            value=os.environ.pop(var,None)
            if use_env and value: self.values[p]=self.clean(value)
    @staticmethod
    def clean(value):
        value=value.strip()
        need(20<=len(value)<=8192 and value.isascii() and not any(c.isspace() for c in value),
             'Empty/malformed credential; paste the API key, not a login password')
        return value
    def get(self,p):
        need(p in CLOUD,'Unexpected secret provider')
        if p not in self.values:
            need(sys.stdin.isatty(),'Run interactively to enter the API key')
            self.values[p]=self.clean(getpass.getpass(p.upper()+'_API_KEY（非表示・保存しません）: '))
        return self.values[p]
    def redact(self,text):
        for key in self.values.values(): text=text.replace(key,'[REDACTED]')
        return text


def allowed_http(provider, method, path):
    if provider not in CLOUD: return False
    if not re.fullmatch(r'/[A-Za-z0-9_/.-]+', path): return False
    if method=='GET' and re.fullmatch(r'/v1/models/[A-Za-z0-9_.-]+', path): return True
    if provider=='openai':
        return bool((method=='POST' and path in ('/v1/responses/input_tokens','/v1/files','/v1/batches'))
          or (method=='GET' and re.fullmatch(r'/v1/(batches/[A-Za-z0-9_-]+|files/[A-Za-z0-9_-]+/content)',path))
          or (method=='POST' and re.fullmatch(r'/v1/batches/[A-Za-z0-9_-]+/cancel',path)))
    return bool((method=='POST' and path in ('/v1/messages/count_tokens','/v1/messages/batches'))
      or (method=='GET' and re.fullmatch(r'/v1/messages/batches/[A-Za-z0-9_-]+(?:/results)?',path))
      or (method=='POST' and re.fullmatch(r'/v1/messages/batches/[A-Za-z0-9_-]+/cancel',path)))


def http_request(provider,method,path,payload,secrets,content_type='application/json',timeout=120):
    need(allowed_http(provider,method,path),'HTTP path blocked (no synchronous generation): '+method+' '+path)
    headers={'Accept':'application/json','Content-Type':content_type}
    key=secrets.get(provider)
    if provider=='openai': headers['Authorization']='Bearer '+key
    else: headers.update({'x-api-key':key,'anthropic-version':'2023-06-01'})
    con=http.client.HTTPSConnection(HOSTS[provider],timeout=timeout,context=ssl.create_default_context())
    start=time.monotonic()
    try:
        # Exactly one network attempt; never follow a redirect with credentials.
        con.request(method,path,body=payload,headers=headers)
        resp=con.getresponse();raw=resp.read(64*1024**2+1)
        need(len(raw)<=64*1024**2,'Oversized API response')
        raw=secrets.redact(raw.decode('utf-8',errors='strict')).encode()
        return {'http_status':resp.status,'raw_body_b64':base64.b64encode(raw).decode(),
           'headers':{k.lower():v for k,v in resp.getheaders() if k.lower() in ('x-request-id','request-id','date','content-type')},
           'provider':provider,'method':method,'path':path,'utc':now(),'wall_seconds':time.monotonic()-start}
    finally: con.close()


def api_http(provider,path,body,secrets,timeout=120):
    return http_request(provider,'GET' if body is None else 'POST',path,None if body is None else canon(body),secrets,timeout=timeout)
M.api_http = api_http


def raw_response(env): return base64.b64decode(env['raw_body_b64'],validate=True)

def response_object(env):
    status=env.get('http_status')
    if status not in (200,201):
        try:
            err=parse(raw_response(env)).get('error',{})
            code=str(err.get('code') or err.get('type') or '')
            code=code if re.fullmatch(r'[A-Za-z0-9_.-]{0,100}',code) else 'redacted'
        except Exception: code='unparsed'
        rid=env.get('headers',{}).get('x-request-id') or env.get('headers',{}).get('request-id') or ''
        rid=rid if re.fullmatch(r'[A-Za-z0-9_.-]{0,160}',rid) else 'redacted'
        message=f"{env.get('provider','API')} HTTP {status}; code={code}; request_id={rid}"
        if status==401: message+='; authentication rejected. Batch does not fix an invalid/revoked/wrong-project key.'
        raise Blocked(message)
    obj=parse(raw_response(env));need(isinstance(obj,dict),'Expected JSON object');return obj
M.response_object = response_object


def authenticate(secrets):
    result={}
    for p in CLOUD:
        result[p]=M.model_lookup(p,M.PRESETS[p],secrets)
        print('BATCH_AUTH_METADATA_OK='+p+' model='+M.PRESETS[p]['id'],flush=True)
    print('NO_GENERATION_SUBMITTED; model lookup is not proof of all Batch permissions',flush=True)
    return result


def make_budget(plan,secrets,root):
    budget=M.make_budget(plan,secrets,root)
    budget.update(sequential_standard_api_not_batch=False, batch_api=True,
                  first_balanced_tranche_only=True, paid_requests=60, later_trials_auto_submitted=False)
    M.validate_budget(plan,budget);return budget


def authorize(plan,budget,limit,root,consent=None):
    limit=money(limit);M.validate_budget(plan,budget)
    need(D(budget['full_cohort_reserved_usd'])<=limit,
         'BUDGET_BLOCK: entire 60-request reservation exceeds your limit. No partial batch or generation sent.')
    ap=root/'authorization.json'
    if ap.exists():
        auth=parse(read(ap));M.validate_budget(plan,budget,auth)
        need(D(auth['max_api_usd'])==limit,'Existing approved limit differs; authorization is immutable')
        return auth
    print(json.dumps({'planned_total_slots':90,'cloud_requests':60,'qwen_requests':30,
       'trials_now':[1],'trials_not_sent':[2,3],'max_output_tokens_per_request':8192,
       'provider_reserved_usd':budget['provider_reserved_usd'],'reserved_usd':budget['full_cohort_reserved_usd'],
       'your_api_budget_usd':str(limit),'not_included':'GPU rental, taxes, FX, unrelated API calls'},ensure_ascii=False,indent=2),flush=True)
    token=consent if consent is not None else input('上の費用・先行1試行・60件のBatch送信を承認する場合だけ START BATCH 60: ').strip()
    need(token=='START BATCH 60','Not approved; no batch generation submitted')
    auth={'approved':True,'plan_sha256':digest(canon(plan)),'budget_sha256':digest(canon(budget)),
       'max_api_usd':str(limit),'full_cohort_reserved_usd':budget['full_cohort_reserved_usd'],
       'price_date':PRICE_DATE,'batch_only':True,'not_a_provider_billing_cap':True,'utc':now()}
    jw(ap,auth);return auth


def provider_requests(plan,p):
    return [r for g in plan['groups'] for r in g['requests'] if r['provider']==p]


def batch_input(plan,p,run_id):
    need(re.fullmatch(r'[0-9a-f]{12}',run_id),'Invalid run identity')
    rows=[];mapping={}
    for r in provider_requests(plan,p):
        cid='g4b-'+run_id+'-'+r['id']
        need(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',cid),'Custom ID invalid/too long')
        need(cid not in mapping,'Duplicate custom ID');mapping[cid]=r['id']
        body=api_payload(p,r,plan['config'])
        rows.append({'custom_id':cid,'method':'POST','url':'/v1/responses','body':body} if p=='openai'
           else {'custom_id':cid,'params':body})
    need(len(rows)==30,'Expected 30 requests per provider')
    raw=b''.join(canon(x) for x in rows) if p=='openai' else canon({'requests':rows})
    return raw,mapping


def multipart(raw,name):
    boundary='gpu004b'+uuid.uuid4().hex
    need(re.fullmatch(r'[A-Za-z0-9_.-]+',name),'Unsafe upload name')
    prefix=(f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
      f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
      'Content-Type: application/jsonl\r\n\r\n').encode()
    return prefix+raw+f'\r\n--{boundary}--\r\n'.encode(),'multipart/form-data; boundary='+boundary


def check_batch_object(p,obj,bd,run_id,plan):
    bid=obj.get('id');need(isinstance(bid,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,160}',bid),'Invalid batch ID')
    need(obj.get('type' if p=='anthropic' else 'object')==('message_batch' if p=='anthropic' else 'batch'),'Wrong batch object')
    if p=='openai':
        fid=parse(read(bd/'file.json'))['id']
        need(obj.get('input_file_id')==fid and obj.get('endpoint')=='/v1/responses','Batch/file/endpoint mismatch')
        md=obj.get('metadata') or {}
        need(md.get('gpu004b_run')==run_id and md.get('plan_sha256')==digest(canon(plan)),'Batch metadata mismatch')
    return bid


def submit_once(plan,budget,auth,root,p,secrets):
    M.validate_budget(plan,budget,auth)
    bd=P.safe(root/'batches'/p);bd.mkdir(parents=True,exist_ok=True)
    run_id=parse(read(root/'run-identity.json'))['run_id']
    raw,mapping=batch_input(plan,p,run_id)
    input_path=bd/('input.jsonl' if p=='openai' else 'input.json')
    if input_path.exists(): need(read(input_path)==raw,'Batch input changed')
    else: save(input_path,raw)
    M.immutable_json(bd/'custom-id-map.json',mapping)
    response_path=bd/'submission-response.json';intent_path=bd/'submission-intent.json'
    if response_path.exists():
        obj=response_object(parse(read(response_path)))
        check_batch_object(p,obj,bd,run_id,plan)
        need(intent_path.exists(),'Submission receipt without intent')
        need(parse(read(intent_path))['input_sha256']==digest(raw),'Submission input pin differs')
        return obj
    need(not intent_path.exists(),
         'SUBMISSION_UNCERTAIN: intent exists without receipt for '+p+'. Do NOT delete it or resubmit; locate the batch ID first.')
    if p=='openai':
        fp=bd/'file.json'
        if fp.exists(): f=parse(read(fp))
        else:
            # Uploading alone does not submit generation. A failed upload is retained as a separate attempt.
            data,typ=multipart(raw,'gpu004b-'+run_id+'.jsonl')
            attempt=bd/('upload-'+uuid.uuid4().hex+'.json')
            env=http_request(p,'POST','/v1/files',data,secrets,content_type=typ)
            jw(attempt,env);f=response_object(env)
            need(f.get('purpose')=='batch' and f.get('bytes')==len(raw),'Uploaded file attributes differ')
            need(re.fullmatch(r'[A-Za-z0-9_-]+',str(f.get('id',''))),'Bad file ID');jw(fp,f)
        request={'input_file_id':f['id'],'endpoint':'/v1/responses','completion_window':'24h',
                 'metadata':{'gpu004b_run':run_id,'plan_sha256':digest(canon(plan))}}
        path='/v1/batches';payload=canon(request)
    else:
        path='/v1/messages/batches';payload=raw
    # This intent is fsynced before the only paid Batch POST. Never infer "not sent" after an exception.
    jw(intent_path,{'provider':p,'run_id':run_id,'input_sha256':digest(raw),
       'payload_sha256':digest(payload),'plan_sha256':digest(canon(plan)),
       'request_count':30,'reserved_usd':budget['provider_reserved_usd'][p],
       'no_automatic_resubmission':True,'utc':now()})
    env=http_request(p,'POST',path,payload,secrets)
    jw(response_path,env)  # HTTP errors are also receipts, not a reason to repeat the POST.
    obj=response_object(env);bid=check_batch_object(p,obj,bd,run_id,plan)
    print('BATCH_SUBMITTED '+p+' id='+bid+' requests=30',flush=True)
    return obj


def parse_jsonl(raw,mapping):
    result={}
    for line in raw.splitlines():
        if not line.strip(): continue
        obj=parse(line);need(isinstance(obj,dict),'Invalid JSONL result')
        cid=obj.get('custom_id');need(cid in mapping,'Unplanned custom_id in batch output')
        need(cid not in result,'Duplicate custom_id in batch output');result[cid]=obj
    return result


def result_packages(plan,p,batch,parts,mapping,budget):
    expected=set(mapping);seen={}
    for raw in parts:
        for cid,item in parse_jsonl(raw,mapping).items():
            need(cid not in seen,'Duplicate ID across output/error files');seen[cid]=item
    terminal=batch.get('status') if p=='openai' else batch.get('processing_status')
    need(terminal in (('completed','expired','cancelled','failed') if p=='openai' else ('ended',)), 'Nonterminal batch')
    if terminal in ('completed','ended'): need(set(seen)==expected,'Terminal batch result missing IDs; preserve files, do not regenerate')
    idx=M.index_requests(plan);packages={}
    for custom,cid in mapping.items():
        r=idx[cid];item=seen.get(custom);body=None;failure=None
        if item is None: failure='batch_'+terminal+'_without_result'
        elif p=='openai':
            resp=item.get('response');err=item.get('error')
            need(not(resp is not None and err is not None),'Conflicting batch response and error')
            if isinstance(resp,dict) and resp.get('status_code')==200 and err is None:
                body=resp.get('body');need(isinstance(body,dict),'Missing Responses body')
            else: failure='batch_request_error'
        else:
            result=item.get('result');need(isinstance(result,dict),'Missing Claude result')
            kind=result.get('type');need(kind in ('succeeded','errored','canceled','expired'),'Unknown Claude result type')
            if kind=='succeeded':
                body=result.get('message');need(isinstance(body,dict),'Missing Claude message')
            else: failure='batch_'+kind
        reservation=budget['per_request'][cid]['reserved_usd']
        pkg={'id':cid,'provider':p,'request_sha256':digest(canon(r)),
             'batch_id':batch['id'],'custom_id':custom,'attempt':1,'batch_only':True,
             'result_record':item,'batch_terminal_state':terminal,'reserved_usd':reservation}
        if failure:
            pkg.update(batch_terminal_failure=True,error=failure,usage_upper_usd=reservation,
                       charge_unknown=True,retained_reservation_not_claimed_charge=True)
        else:
            pkg['envelope']={'http_status':200,'raw_body_b64':base64.b64encode(canon(body)).decode(),
                'source':'body of downloaded batch result; not a new synchronous request'}
            try:
                upper=M.usage_upper(p,body,plan['config']['models'][p])
                pkg.update(usage_upper_usd=upper,charge_unknown=False)
            except Blocked:
                pkg.update(usage_upper_usd=reservation,charge_unknown=True,missing_usage=True)
            pkg['over_reserved_cost_observed']=D(pkg['usage_upper_usd'])>D(reservation)
        packages[cid]=pkg
    return packages


def batch_path(p,bid):
    need(re.fullmatch(r'[A-Za-z0-9_-]{1,160}',bid),'Unsafe batch ID')
    return ('/v1/batches/' if p=='openai' else '/v1/messages/batches/')+bid


def verify_materialized(root,p):
    bd=root/'batches'/p;mp=bd/'materialized.json'
    if not mp.exists():return False
    pin=parse(read(mp))
    for rel,h in pin['files'].items():
        path=Path(rel);need(not path.is_absolute() and '..' not in path.parts,'Unsafe result manifest path')
        need(hfile(root/path)==h,'Local batch result altered: '+rel)
    return True


def poll_and_collect(plan,budget,root,p,secrets):
    bd=root/'batches'/p
    if verify_materialized(root,p): return True
    if not (bd/'submission-response.json').exists(): return False
    submitted=response_object(parse(read(bd/'submission-response.json')))
    bid=submitted['id'];env=api_http(p,batch_path(p,bid),None,secrets);obj=response_object(env)
    need(obj.get('id')==bid,'Batch ID changed on retrieval')
    check_batch_object(p,obj,bd,parse(read(root/'run-identity.json'))['run_id'],plan)
    P.atomic(bd/'latest-status.json',env)
    state=obj.get('status' if p=='openai' else 'processing_status')
    print('BATCH_STATUS '+p+' '+str(state),flush=True)
    if p=='openai':
        need(state in ('validating','in_progress','finalizing','cancelling','completed','expired','cancelled','failed'),'Unknown OpenAI batch state')
        if state not in ('completed','expired','cancelled','failed'):return False
    else:
        need(state in ('in_progress','canceling','ended'),'Unknown Claude batch state')
        if state!='ended':return False
    raws=[];files={}
    def get_result(path,name):
        dest=bd/name
        if dest.exists(): raw=read(dest,64*1024**2)
        else:
            e=api_http(p,path,None,secrets)
            if e['http_status']!=200: response_object(e)
            raw=raw_response(e);save(dest,raw)
        files[dest.relative_to(root).as_posix()]=digest(raw);raws.append(raw)
    if p=='openai':
        for field in ('output_file_id','error_file_id'):
            fid=obj.get(field)
            if fid:
                need(re.fullmatch(r'[A-Za-z0-9_-]+',fid),'Invalid result file ID')
                get_result('/v1/files/'+fid+'/content',field+'.jsonl')
    else:
        # Results URL is not trusted as a credential destination. Require the documented same-host endpoint.
        path=batch_path(p,bid)+'/results'
        need(obj.get('results_url')=='https://api.anthropic.com'+path,'Unexpected Claude results URL; no redirect followed')
        get_result(path,'results.jsonl')
    mapping=parse(read(bd/'custom-id-map.json'))
    packets=result_packages(plan,p,obj,raws,mapping,budget)
    for cid,pkg in packets.items():
        dest=root/'api-ledger'/cid/'package.json';M.immutable_json(dest,pkg)
        files[dest.relative_to(root).as_posix()]=hfile(dest)
    M.immutable_json(bd/'terminal.json',obj);files[(bd/'terminal.json').relative_to(root).as_posix()]=hfile(bd/'terminal.json')
    jw(bd/'materialized.json',{'batch_id':bid,'provider':p,'requests':len(packets),'files':files,'utc':now()})
    print('BATCH_RESULTS_LOCAL_VERIFIED '+p+' requests='+str(len(packets)),flush=True)
    return True


def spending_report(root,budget):
    known=D(0);unresolved=D(0);resolved=0
    for cid,rule in budget['per_request'].items():
        path=root/'api-ledger'/cid/'package.json'
        if path.exists():
            pkg=parse(read(path));v=D(pkg['usage_upper_usd'])
            need(v.is_finite() and v>=0,'Invalid recorded cost')
            if pkg.get('charge_unknown'):unresolved+=v
            else:known+=v;resolved+=1
        elif (root/'batches'/rule['provider']/'submission-intent.json').exists():unresolved+=D(rule['reserved_usd'])
    return {'usage_known_requests':resolved,'known_usage_cost_upper_usd':str(known),
       'unreconciled_reserved_usd':str(unresolved),'upper_including_unreconciled_usd':str(known+unresolved),
       'not_an_invoice':True,'not_provider_hard_cap':True,'rates':BATCH_PRICES,
       'excludes_gpu_rental_tax_fx_other_api_uses':True,'utc':now()}


def generate_group(plan,g,A,assets):
    if g['provider']=='qwen':return _ORIGINAL_GENERATE(plan,g,A,assets)
    d=ROOT/'groups'/g['label'];P.public_dirs(d);records=[];p=g['provider']
    for r in g['requests']:
        rd=d/'generation'/r['condition'];P.public_dirs(rd)
        rec={k:r[k] for k in ('id','provider','task','condition','trial','seed','seed_sent_to_provider','messages_sha256')}
        rec.update(model=plan['config']['models'][p]['id'],generation_status='invalid_generation',error=None)
        jw(rd/'request.json',r);P.update(phase='IMPORTING_BATCH_RESULT',current_id=r['id'])
        package=M.wait_cloud(r);jw(rd/'api-package.json',package)
        need(package.get('provider')==p and package.get('batch_only') is True,'Nonbatch/wrong provider package')
        rec.update(batch_id=package['batch_id'],custom_id=package['custom_id'],transport='batch',
                   token_cost_upper_usd=package['usage_upper_usd'])
        if package.get('batch_terminal_failure'):
            rec.update(generation_status='batch_terminal_failure',error=package['error'])
        else:
            obj=response_object(package['envelope']);jw(rd/'response.json',obj);rec['usage']=obj.get('usage',{})
            try:
                text=M.cloud_text(p,obj,plan['config']);source,block=M.parse_candidate(text,r['task'])
                save(rd/'candidate.cu',source.encode())
                rec.update(generation_status='saved',source_sha256=digest(source.encode()),
                           source_equals_original=source==M.original(r['task']),block=block)
            except NumericFailure as e:rec['error']=str(e)
        P.update(generation_calls=P.STATE.get('generation_calls',0)+1)
        jw(rd/'record.json',rec);records.append(rec)
        print('GPU004B_BATCH_RESULT_TERMINAL '+r['id']+' '+rec['generation_status'],flush=True)
    jw(d/'model-stopped.json',{'model_not_started_for_cloud_group':True,'utc':now()});P.no_other_gpu()
    return records
M.generate_group = generate_group


def summarize(outcomes,plan):
    need(len(outcomes)==len({o['id'] for o in outcomes})==90 and {o['id'] for o in outcomes}==set(M.index_requests(plan)), '90-slot accounting gap')
    by={};rows=[]
    for p in M.PROVIDERS:
        sub=[o for o in outcomes if o['provider']==p]
        valid=[m for o in sub for m in o['measurements'] if m['measurement_valid']]
        by[p]={'model':plan['config']['models'][p]['id'],'candidate_slots':len(sub),
            'generation_status_counts':dict(Counter(o['generation_status'] for o in sub)),
            'correctness_passed':sum(o['correctness_passed'] for o in sub),
            'valid_size_measurements':len(valid),'size_speedups_gt_1_02':sum(m['speedup_gt_1_02'] for m in valid),
            'same_source_saved':sum(o.get('source_equals_original',False) for o in sub)}
    for o in outcomes:
        for m in o['measurements'] or [{}]:
            rows.append({k:o.get(k) for k in ('id','provider','model','task','condition','trial','generation_status','stage','correctness_passed','source_equals_original','block','error')}|m)
    summary={'state':'GPU004B_FIRST_TRIAL_90_COMPLETE','candidate_slots':90,'providers':by,
         'cloud_batch_requests_planned':60,'qwen_requests_planned':30,'independent_workloads':6,
         'trial_numbers':[1],'unsubmitted_trial_numbers':[2,3],'prior_270_plan_complete':False,
         'cloud_generation_transport':'batch_only','no_synchronous_cloud_generation':True,
         'common_prompt_content':True,'numeric_core_sha256':M.CORE_SHA,'no_error_tolerance_changes':True,
         'no_best_of_selection':True,'no_automatic_next_tranche':True,'old_results_overwritten':False,
         'formal_equivalence_proven':False,'whole_GPU_study_complete':False,'utc':now()}
    d=ROOT/'final';jw(d/'summary.json',summary);jw(d/'outcomes.json',outcomes);jw(d/'protocol.json',plan)
    save(d/'outcomes.csv',M.csv_bytes(rows));return summary
M.summarize = summarize


def prepare(con,root,secrets,limit):
    if (root/'plan.json').exists():
        plan=parse(read(root/'plan.json'));M.validate_plan(plan)
    else:
        cfg=cfg_document();M.validate_settings(cfg)
        env=parse(con.run(M.remote_cmd('--_probe')));plan=make_plan(cfg,env)
        jw(root/'plan.json',plan);jw(root/'models.json',cfg)
    if not(root/'run-identity.json').exists():jw(root/'run-identity.json',{'run_id':uuid.uuid4().hex[:12],'utc':now()})
    if (root/'budget.json').exists():budget=parse(read(root/'budget.json'))
    else:
        tmp=root/('cost-preflight-'+uuid.uuid4().hex)
        budget=make_budget(plan,secrets,tmp);jw(root/'budget.json',budget)
    auth=authorize(plan,budget,limit,root)
    con.run(M.remote_cmd('--_put-plan'),data=canon({'plan':plan,'authorization':auth}))
    return plan,budget,auth


def process_batches(plan,budget,auth,root,secrets):
    M.validate_budget(plan,budget,auth)
    for p in CLOUD:submit_once(plan,budget,auth,root,p,secrets)
    for p in CLOUD:poll_and_collect(plan,budget,root,p,secrets)
    report=spending_report(root,budget);P.atomic(root/'api-usage-upper.json',report)
    need(D(report['upper_including_unreconciled_usd'])<=D(auth['max_api_usd']),
         'Observed/reserved usage exceeds approval; batches already sent may still run. No further paid submissions.')


def local(mode,allow=False,limit='5',use_env=False):
    need(os.geteuid()!=0,'Run from WSL as the regular user, without sudo')
    secrets=Secrets(use_env);root=M.local_root()
    if mode in ('run','auth-check'):authenticate(secrets)
    if mode=='auth-check':return
    A=P.module_a();A.fingerprint_check(Path.home()/'.ssh/id_ed25519');con=A.Connection()
    try:
        with P.lock(root/'local-controller.lock'):
            if mode=='run':
                need(allow,'Explicit temporary disk/local checkpoint permission required')
                raw=read(__file__)
                print(con.run(['/usr/bin/python3','-I','-S','-B','-c',P.install_text(digest(raw))],data=raw).decode())
                plan,budget,auth=prepare(con,root,secrets,limit)
                doc=parse(con.run(M.remote_cmd('--_launch','--allow-ephemeral-with-local-checkpoints')))
                print('GPU004B_BATCH_PIPELINE_STARTED; 90 slots in first balanced trial; no automatic later trials',flush=True)
            else:
                plan=parse(read(root/'plan.json'));M.validate_plan(plan)
                budget=parse(read(root/'budget.json'));auth=parse(read(root/'authorization.json'))
                M.validate_budget(plan,budget,auth)
                doc=parse(con.run(M.remote_cmd('--_status')))
            seen=set();next_poll=0;last=None;idx=M.index_requests(plan)
            while True:
                need(doc.get('plan_sha256')==digest(canon(plan)),'Remote plan differs')
                if mode=='status':
                    print(json.dumps(doc,ensure_ascii=False,indent=2));print(json.dumps(spending_report(root,budget),indent=2));return
                for rec in doc['receipts']:
                    if rec['label'] not in seen:
                        P.checkpoint_collect(con,rec);seen.add(rec['label'])
                        print('GPU004B_LOCAL_CHECKPOINT_VERIFIED '+rec['label'],flush=True)
                public={'state':doc['state'],**doc.get('progress',{})}
                rendered=json.dumps(public,ensure_ascii=False,sort_keys=True)
                if rendered!=last:print(rendered,flush=True);last=rendered
                if doc['state'] in ('BLOCKED','INTERRUPTED'):
                    P.atomic(root/'last-status.json',doc)
                    print(json.dumps(doc.get('failure',{}),ensure_ascii=False,indent=2))
                    raise Blocked('GPU worker stopped. Existing cloud batches are NOT canceled automatically; no automatic regeneration or timing retry.')
                if doc['state']=='COMPLETE':
                    need(all(verify_materialized(root,p) for p in CLOUD),'Cloud results not yet verified locally')
                    P.atomic(root/'final-status.json',doc);P.atomic(root/'api-usage-upper.json',spending_report(root,budget))
                    print(json.dumps(doc['summary'],ensure_ascii=False,indent=2))
                    print('GPU004B_FIRST_TRIAL_LOCAL_COPY_VERIFIED; 90/90 in this tranche, NOT 270/270',flush=True);return
                need(doc['state']=='RUNNING','Worker not running')
                if mode=='collect':return
                # No paid request before the actual original-CUDA controls have passed AND been backed up.
                if 'original-controls' in seen and time.monotonic()>=next_poll:
                    process_batches(plan,budget,auth,root,secrets);next_poll=time.monotonic()+BATCH_POLL_SECONDS
                pending=doc.get('pending_cloud')
                if pending:
                    r=idx.get(pending['id']);need(r and r['provider'] in CLOUD,'Unknown pending batch request')
                    need(pending['request_sha256']==digest(canon(r)),'Pending request modified')
                    if verify_materialized(root,r['provider']):
                        pkg=parse(read(root/'api-ledger'/r['id']/'package.json'))
                        con.run(M.remote_cmd('--_supply',r['id']),data=canon(pkg))
                time.sleep(5);doc=parse(con.run(M.remote_cmd('--_status')))
    except KeyboardInterrupt:
        print('WATCH_CLOSED; cloud batches continue once submitted. --watch only resumes polling/import. Pod billing continues.')
    finally:con.close()


def cancel_batches(use_env=False):
    need(os.geteuid()!=0,'Run locally, without sudo');secrets=Secrets(use_env);root=M.local_root()
    known=[]
    for p in CLOUD:
        fp=root/'batches'/p/'submission-response.json'
        if fp.exists():known.append((p,response_object(parse(read(fp)))['id']))
    need(known,'No saved batch IDs; do not guess or resubmit')
    print('Saved batches:',known)
    need(input('未完了のBatchを取り消す場合だけ CANCEL BATCHES: ').strip()=='CANCEL BATCHES','Not confirmed')
    with P.lock(root/'local-controller.lock'):
        for p,bid in known:
            fp=root/'batches'/p/'cancel-response.json'
            if fp.exists():print('CANCEL_ALREADY_RECORDED',p);continue
            status=response_object(api_http(p,batch_path(p,bid),None,secrets))
            state=status.get('status' if p=='openai' else 'processing_status')
            if state in ('completed','expired','cancelled','failed','ended'):print('ALREADY_TERMINAL',p,state);continue
            intent=fp.with_name('cancel-intent.json')
            need(not intent.exists(),'Previous cancel is uncertain; inspect saved batch status, no automatic POST repetition')
            jw(intent,{'batch_id':bid,'utc':now()})
            env=api_http(p,batch_path(p,bid)+'/cancel',{},secrets);jw(fp,env);response_object(env)
    print('BATCH_CANCEL_REQUESTED; in-flight work may still complete and cost money. No Pod deletion or data deletion.')


def main():
    # Internal worker/numeric/checkpoint commands are dispatched by the pinned runner.
    if any(x.startswith('--_') for x in sys.argv[1:]):M.main();return
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True)
    for x in ('run','watch','collect','status','auth-check','self-test','numeric-core-self-test','cancel-batches'):
        g.add_argument('--'+x,action='store_true')
    ap.add_argument('--api-budget-usd',default='5')
    ap.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true')
    ap.add_argument('--use-env-keys',action='store_true',help='Explicitly use API key environment variables; otherwise prompt afresh')
    args=ap.parse_args()
    if args.self_test:self_test();return
    if args.numeric_core_self_test:C.self_test();return
    if args.cancel_batches:cancel_batches(args.use_env_keys);return
    mode=next(x for x in ('run','watch','collect','status','auth_check') if getattr(args,x))
    local(mode.replace('_','-'),args.allow_ephemeral_with_local_checkpoints,args.api_budget_usd,args.use_env_keys)

def fixture_environment():
    return {'gpu':{'name':'NVIDIA A40','compute_capability':[8,6],'warp_size':32,
        'static_shared_memory_per_block':49152,'registers_per_block':65536,
        'max_threads_per_multiprocessor':1536,'shared_memory_per_multiprocessor':102400,
        'multiprocessors':84,'l2_bytes':6291456,'max_threads_per_block':1024,'memory_bytes':48305799168},
        'gpu_uuid':P.EXPECTED_GPU,'driver_version':'570.195.03','nvrtc_version':[12,8],
        'nvrtc_sha256':'a'*64,'sanitizer_sha256':'b'*64,'host_compiler':'fixture-g++',
        'core_sha256':M.CORE_SHA,'os_release':'fixture-linux','observed_utc':'fixture',
        'free_disk_bytes':10*1024**3,'storage_persistence_verified':False}


def fixture_budget(plan,count=2000):
    rules={r['id']:{**M.reserve_cost(count,plan['config']['models'][r['provider']]),
             'provider':r['provider'],'request_sha256':digest(canon(api_payload(r['provider'],r,plan['config'])))}
           for r in M.index_requests(plan).values() if r['provider'] in CLOUD}
    totals={p:sum((D(x['reserved_usd']) for x in rules.values() if x['provider']==p),D(0)) for p in CLOUD}
    return {'schema':VERSION,'plan_sha256':digest(canon(plan)),'per_request':rules,
            'provider_reserved_usd':{p:str(x) for p,x in totals.items()},
            'full_cohort_reserved_usd':str(sum(totals.values(),D(0)))}


def self_test():
    import tempfile
    this=sys.modules[__name__]
    class Tests(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.cfg=cfg_document();cls.env=fixture_environment();cls.plan0=make_plan(cls.cfg,cls.env)
        def setUp(self):
            self.tmp=tempfile.TemporaryDirectory(prefix='gpu004b-tests-')
            self.old=ROOT;configure(Path(self.tmp.name)/'remote');ROOT.mkdir()
            self.root=Path(self.tmp.name)/'local';self.root.mkdir()
            self.plan=copy.deepcopy(self.plan0);self.budget=fixture_budget(self.plan)
            self.auth={'approved':True,'plan_sha256':digest(canon(self.plan)),
               'budget_sha256':digest(canon(self.budget)),'max_api_usd':'5'}
            self.run='123456789abc';jw(self.root/'run-identity.json',{'run_id':self.run})
            self.idx=M.index_requests(self.plan);self.secrets=Secrets()
            self.secrets.values={'openai':'test-openai-secret-1234567890','anthropic':'test-anthropic-secret-1234567890'}
        def tearDown(self):configure(self.old);P.WORK_DEADLINE=None;self.tmp.cleanup()
        def envp(self,obj,status=200):return {'http_status':status,'raw_body_b64':base64.b64encode(canon(obj)).decode(),'provider':'fixture','headers':{}}
        def resultbody(self,p,r):
            text=json.dumps({'block':C.SPECS[r['task']]['base']})+'\n'+M.original(r['task'])
            if p=='openai':return {'model':self.cfg['models'][p]['id'],'status':'completed','usage':{'input_tokens':2000,'output_tokens':300},
                  'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':text}]}]}
            return {'type':'message','model':self.cfg['models'][p]['id'],'stop_reason':'end_turn',
                'usage':{'input_tokens':2000,'output_tokens':300},'content':[{'type':'text','text':text}]}
        def resultlines(self,p):
            _,mapping=batch_input(self.plan,p,self.run);out=[]
            for custom,cid in mapping.items():
                body=self.resultbody(p,self.idx[cid])
                out.append({'custom_id':custom,'response':{'status_code':200,'body':body},'error':None} if p=='openai' else
                           {'custom_id':custom,'result':{'type':'succeeded','message':body}})
            return out,mapping
        def batch(self,p):
            if p=='openai':return {'id':'batch_test','object':'batch','status':'completed','input_file_id':'file_test','endpoint':'/v1/responses',
              'metadata':{'gpu004b_run':self.run,'plan_sha256':digest(canon(self.plan))},'output_file_id':'file_out','error_file_id':None}
            return {'id':'msgbatch_test','type':'message_batch','processing_status':'ended',
                    'results_url':'https://api.anthropic.com/v1/messages/batches/msgbatch_test/results'}
        def install_submission(self,p):
            bd=self.root/'batches'/p;bd.mkdir(parents=True,exist_ok=True)
            raw,mapping=batch_input(self.plan,p,self.run)
            save(bd/('input.jsonl' if p=='openai' else 'input.json'),raw);jw(bd/'custom-id-map.json',mapping)
            jw(bd/'submission-intent.json',{'input_sha256':digest(raw)})
            jw(bd/'submission-response.json',self.envp(self.batch(p)))
            if p=='openai':jw(bd/'file.json',{'id':'file_test'})
            return bd
        def packets(self,p):
            lines,mapping=self.resultlines(p)
            return result_packages(self.plan,p,self.batch(p),[b''.join(canon(x) for x in lines)],mapping,self.budget)
        def test_embedded_parent_hash(self):self.assertEqual(digest(BASE_RAW),BASE_SHA)
        def test_unchanged_numeric_core_hash(self):
            self.assertEqual(M.CORE_SHA,'afe6858e7d510084a40e97aa81c14fa9da907fc80bc23f4a8b76f1eccf14e90a')
            self.assertEqual(digest(gzip.decompress(base64.b64decode(M.CORE_EMBED))),M.CORE_SHA)
        def test_balanced_first_trial(self):
            self.assertEqual(len(self.idx),90)
            self.assertEqual(Counter(r['provider'] for r in self.idx.values()),{'qwen':30,'openai':30,'anthropic':30})
            self.assertEqual({r['trial'] for r in self.idx.values()},{1})
        def test_all_six_tasks_all_five_arms(self):
            for p in M.PROVIDERS:
                self.assertEqual({(r['task'],r['condition']) for r in provider_requests(self.plan,p)},
                                 {(t,a) for t in C.TASKS for a in C.ARMS})
        def test_cross_model_prompts_identical(self):
            for t in C.TASKS:
                for a in C.ARMS:
                    self.assertEqual(len({r['messages_sha256'] for r in self.idx.values() if r['task']==t and r['condition']==a}),1)
        def test_prompt_preserved_from_prior_runner(self):
            for r in self.idx.values():self.assertEqual(r['messages'],M.messages_for(r['task'],r['condition'],self.env))
        def test_p0_no_gpu_leak(self):
            for r in self.idx.values():
                if r['condition']=='P0':
                    for s in ('A40','sm_86','V100'):self.assertNotIn(s,canon(r['messages']).decode())
        def test_no_paid_request_before_acceptance_assertion(self):
            import inspect
            s=inspect.getsource(local)
            self.assertIn("if 'original-controls' in seen",s)
        def test_qwen_groups_first(self):
            self.assertEqual([g['provider'] for g in self.plan['groups'][:6]],['qwen']*6)
            self.assertTrue(all(g['provider']!='qwen' for g in self.plan['groups'][6:]))
        def test_output_cap_not_lowered(self):self.assertEqual({v['max_output_tokens'] for v in self.cfg['models'].values()},{8192})
        def test_budget_validation(self):M.validate_budget(self.plan,self.budget,self.auth)
        def test_output_only_reservation_arithmetic(self):
            self.assertEqual(D(30)*8192*(D(6)+D('7.5'))/D(1000000),D('3.31776'))
        def test_price_rates(self):self.assertEqual(BATCH_PRICES,{'openai':('1','6'),'anthropic':('1.50','7.50')})
        def test_small_budget_blocks_before_consent(self):
            with mock.patch('builtins.input',side_effect=AssertionError('must not ask')):
                with self.assertRaises(Blocked):authorize(self.plan,self.budget,'1',self.root)
        def test_budget_nan_inf_negative_refused(self):
            for v in ('NaN','Inf','-1','0','101'):
                with self.assertRaises(Blocked):money(v)
        def test_authorization_requires_exact_consent(self):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(Blocked):authorize(self.plan,self.budget,'5',self.root,'yes')
        def test_authorization_created_then_not_changed(self):
            with contextlib.redirect_stdout(io.StringIO()):auth=authorize(self.plan,self.budget,'5',self.root,'START BATCH 60')
            self.assertEqual(authorize(self.plan,self.budget,'5',self.root),auth)
            with self.assertRaises(Blocked):authorize(self.plan,self.budget,'6',self.root)
        def test_sync_endpoints_blocked(self):
            for p,path in [('openai','/v1/responses'),('openai','/v1/chat/completions'),('anthropic','/v1/messages')]:
                self.assertFalse(allowed_http(p,'POST',path))
                with self.assertRaises(Blocked):http_request(p,'POST',path,b'{}',self.secrets)
        def test_approved_endpoints(self):
            for p,method,path in [('openai','POST','/v1/batches'),('openai','GET','/v1/files/file_x/content'),
              ('openai','POST','/v1/responses/input_tokens'),('anthropic','POST','/v1/messages/batches'),
              ('anthropic','GET','/v1/messages/batches/msgbatch_x/results')]:self.assertTrue(allowed_http(p,method,path))
        def test_foreign_urls_and_traversal_refused(self):
            for path in ('https://evil.test/v1/models/x','/v1/batches/x?secret=foo','/v1/batches/../../x'):
                self.assertFalse(allowed_http('openai','GET',path))
        def test_credentials_prompt_mode_drops_env(self):
            with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'old-invalid-key-123456789','ANTHROPIC_API_KEY':'old-invalid-key-987654321'}):
                x=Secrets();self.assertEqual(x.values,{});self.assertNotIn('OPENAI_API_KEY',os.environ)
        def test_key_strip_and_redaction(self):
            self.assertEqual(Secrets.clean('  '+'a'*30+'  '),'a'*30)
            for p,val in self.secrets.values.items():self.assertNotIn(val,self.secrets.redact('x'+val+'y'))
        def test_401_no_error_message_key_leak(self):
            e=self.envp({'error':{'code':'invalid_api_key','message':self.secrets.values['openai']}},401)
            with self.assertRaises(Blocked) as cm:response_object(e)
            self.assertIn('401',str(cm.exception));self.assertNotIn(self.secrets.values['openai'],str(cm.exception))
        def test_auth_failure_has_no_ssh_or_generation(self):
            with mock.patch.object(M,'api_http',return_value=self.envp({'error':{'code':'invalid_api_key'}},401)) as f:
                with self.assertRaises(Blocked):authenticate(self.secrets)
            self.assertEqual(f.call_count,1);self.assertTrue(f.call_args.args[1].startswith('/v1/models/'))
        def test_batch_inputs_30_unique_bounded_ids(self):
            for p in CLOUD:
                raw,mp=batch_input(self.plan,p,self.run);self.assertEqual(len(mp),30)
                self.assertTrue(all(len(x)<=64 for x in mp))
                if p=='openai':self.assertEqual(len(raw.splitlines()),30)
                else:self.assertEqual(len(parse(raw)['requests']),30)
        def test_payload_sampling_and_prompt_preserved(self):
            for p in CLOUD:
                r=provider_requests(self.plan,p)[0];a=_ORIGINAL_PAYLOAD(p,r,self.cfg);b=api_payload(p,r,self.cfg)
                a.pop('service_tier',None);self.assertEqual(a,b)
        def test_multipart_no_plain_generation(self):
            raw=b'{"custom_id":"x"}\n';out,typ=multipart(raw,'fixture.jsonl')
            self.assertIn(b'name="purpose"\r\n\r\nbatch',out);self.assertIn(raw,out);self.assertIn('boundary=',typ)
        def test_unordered_openai_results_mapped_by_id(self):
            lines,mp=self.resultlines('openai');a=result_packages(self.plan,'openai',self.batch('openai'),
               [b''.join(canon(x) for x in reversed(lines))],mp,self.budget)
            self.assertEqual(set(a),set(mp.values()));self.assertTrue(all(not x.get('batch_terminal_failure') for x in a.values()))
        def test_unordered_anthropic_results(self):
            lines,mp=self.resultlines('anthropic');a=result_packages(self.plan,'anthropic',self.batch('anthropic'),
               [b''.join(canon(x) for x in reversed(lines))],mp,self.budget);self.assertEqual(len(a),30)
        def test_duplicate_result_refused(self):
            lines,mp=self.resultlines('openai')
            with self.assertRaises(Blocked):parse_jsonl(canon(lines[0])*2,mp)
        def test_unknown_id_refused(self):
            with self.assertRaises(Blocked):parse_jsonl(b'{"custom_id":"wrong"}\n',{})
        def test_missing_completed_result_refused(self):
            lines,mp=self.resultlines('openai')
            with self.assertRaises(Blocked):result_packages(self.plan,'openai',self.batch('openai'),[canon(lines[0])],mp,self.budget)
        def test_missing_ended_claude_result_refused(self):
            _,mp=self.resultlines('anthropic')
            with self.assertRaises(Blocked):result_packages(self.plan,'anthropic',self.batch('anthropic'),[],mp,self.budget)
        def test_expired_missing_explicitly_accounted_not_regenerated(self):
            _,mp=self.resultlines('openai');b=self.batch('openai');b['status']='expired'
            a=result_packages(self.plan,'openai',b,[],mp,self.budget)
            self.assertEqual(len(a),30);self.assertTrue(all(x['batch_terminal_failure'] and x['charge_unknown'] for x in a.values()))
        def test_claude_terminal_errors_preserved(self):
            lines,mp=self.resultlines('anthropic')
            for j,k in enumerate(('errored','canceled','expired')):lines[j]['result']={'type':k}
            a=result_packages(self.plan,'anthropic',self.batch('anthropic'),[b''.join(canon(x) for x in lines)],mp,self.budget)
            self.assertEqual(sum(x.get('batch_terminal_failure',False) for x in a.values()),3)
        def test_duplicate_across_error_files_refused(self):
            lines,mp=self.resultlines('openai')
            with self.assertRaises(Blocked):result_packages(self.plan,'openai',self.batch('openai'),[canon(lines[0]),canon(lines[0])],mp,self.budget)
        def test_nonterminal_cannot_collect(self):
            b=self.batch('openai');b['status']='in_progress';_,mp=self.resultlines('openai')
            with self.assertRaises(Blocked):result_packages(self.plan,'openai',b,[],mp,self.budget)
        def test_missing_usage_keeps_reservation(self):
            lines,mp=self.resultlines('openai');lines[0]['response']['body'].pop('usage')
            a=result_packages(self.plan,'openai',self.batch('openai'),[b''.join(canon(x) for x in lines)],mp,self.budget)
            cid=mp[lines[0]['custom_id']];self.assertTrue(a[cid]['charge_unknown'])
            self.assertEqual(a[cid]['usage_upper_usd'],self.budget['per_request'][cid]['reserved_usd'])
        def test_intent_without_receipt_never_posts(self):
            bd=self.root/'batches/openai';bd.mkdir(parents=True);jw(bd/'submission-intent.json',{'uncertain':True})
            with mock.patch.object(this,'http_request',side_effect=AssertionError('No POST')):
                with self.assertRaises(Blocked):submit_once(self.plan,self.budget,self.auth,self.root,'openai',self.secrets)
        def test_existing_batch_never_posts(self):
            self.install_submission('openai')
            with mock.patch.object(this,'http_request',side_effect=AssertionError('No POST')):
                obj=submit_once(self.plan,self.budget,self.auth,self.root,'openai',self.secrets)
            self.assertEqual(obj['id'],'batch_test')
        def test_creation_response_lost_never_resubmitted(self):
            def transport(p,method,path,payload,s,**kw):
                if path=='/v1/files':
                    raw,_=batch_input(self.plan,'openai',self.run)
                    return self.envp({'id':'file_test','purpose':'batch','bytes':len(raw)})
                raise TimeoutError('fixture uncertain create')
            with mock.patch.object(this,'http_request',side_effect=transport):
                with self.assertRaises(TimeoutError):submit_once(self.plan,self.budget,self.auth,self.root,'openai',self.secrets)
            with mock.patch.object(this,'http_request',side_effect=AssertionError('No second POST')):
                with self.assertRaises(Blocked):submit_once(self.plan,self.budget,self.auth,self.root,'openai',self.secrets)
        def test_failed_creation_retained_no_fallback(self):
            bd=self.root/'batches/anthropic';bd.mkdir(parents=True)
            with mock.patch.object(this,'http_request',return_value=self.envp({'error':{'type':'invalid_request_error'}},400)) as f:
                with self.assertRaises(Blocked):submit_once(self.plan,self.budget,self.auth,self.root,'anthropic',self.secrets)
                with self.assertRaises(Blocked):submit_once(self.plan,self.budget,self.auth,self.root,'anthropic',self.secrets)
            self.assertEqual(f.call_count,1)
        def test_budget_checked_before_submission(self):
            auth=copy.deepcopy(self.auth);auth['max_api_usd']='1'
            with mock.patch.object(this,'http_request',side_effect=AssertionError('No POST')):
                with self.assertRaises(Blocked):submit_once(self.plan,self.budget,auth,self.root,'anthropic',self.secrets)
        def test_batch_foreign_metadata_refused(self):
            bd=self.install_submission('openai');b=self.batch('openai');b['metadata']['gpu004b_run']='other'
            with self.assertRaises(Blocked):check_batch_object('openai',b,bd,self.run,self.plan)
        def test_result_foreign_url_no_credential_fetch(self):
            self.install_submission('anthropic');b=self.batch('anthropic');b['results_url']='https://evil.test/results'
            with mock.patch.object(this,'api_http',return_value=self.envp(b)) as f:
                with self.assertRaises(Blocked):poll_and_collect(self.plan,self.budget,self.root,'anthropic',self.secrets)
            self.assertEqual(f.call_count,1)
        def test_poll_download_then_cached_verified(self):
            for p in CLOUD:
                self.install_submission(p);lines,_=self.resultlines(p);raw=b''.join(canon(x) for x in lines)
                def fake(provider,path,body,secrets):
                    if path.endswith('/content') or path.endswith('/results'):
                        return {'http_status':200,'raw_body_b64':base64.b64encode(raw).decode()}
                    return self.envp(self.batch(p))
                with mock.patch.object(this,'api_http',side_effect=fake):self.assertTrue(poll_and_collect(self.plan,self.budget,self.root,p,self.secrets))
                with mock.patch.object(this,'api_http',side_effect=AssertionError('No download')):
                    self.assertTrue(poll_and_collect(self.plan,self.budget,self.root,p,self.secrets))
        def test_materialized_tamper_refused(self):
            self.test_poll_download_then_cached_verified()
            path=next((self.root/'api-ledger').glob('openai*/package.json'));path.write_text('{}')
            with self.assertRaises(Blocked):verify_materialized(self.root,'openai')
        def test_no_model_fallback(self):
            cfg=copy.deepcopy(self.cfg);cfg['models']['openai']['id']='different-model'
            with self.assertRaises(Blocked):M.validate_settings(cfg)
        def test_full_batch_submission_only_two_paid_posts(self):
            calls=[]
            def fake(p,method,path,payload,secrets,**kwargs):
                calls.append((p,method,path))
                if path=='/v1/files':
                    raw,_=batch_input(self.plan,p,self.run)
                    return self.envp({'id':'file_test','purpose':'batch','bytes':len(raw)})
                return self.envp(self.batch(p))
            with mock.patch.object(this,'http_request',side_effect=fake):
                for _ in range(2):
                    for p in CLOUD:submit_once(self.plan,self.budget,self.auth,self.root,p,self.secrets)
            self.assertEqual(calls,[('openai','POST','/v1/files'),('openai','POST','/v1/batches'),('anthropic','POST','/v1/messages/batches')])
        def test_batch_terminal_failures_not_correctness_failures(self):
            g=next(g for g in self.plan['groups'] if g['provider']=='anthropic')
            packets=self.packets('anthropic');packets[g['requests'][0]['id']].update(batch_terminal_failure=True,error='batch_expired')
            with mock.patch.object(M,'wait_cloud',side_effect=lambda r:packets[r['id']]),mock.patch.object(P,'no_other_gpu',lambda:None):
                rows=generate_group(self.plan,g,None,None)
            self.assertEqual(rows[0]['generation_status'],'batch_terminal_failure')
            self.assertEqual(sum(r['generation_status']=='saved' for r in rows),4)
        def test_full_worker_90_slots_real_parsers_archives_mock_gpu(self):
            ROOT.joinpath('control').mkdir();save(ROOT/'control/runner.py',read(__file__))
            jw(M.plan_path(),self.plan);jw(ROOT/'control/authorization.json',self.auth)
            packets=self.packets('openai')|self.packets('anthropic')
            env=self.env;test=self
            class Model:
                SAMPLING={'temperature':0.2,'top_p':0.9,'top_k':40,'min_p':0.0}
                def cached_assets(self):return (None,None,None,{'fixture':True},None,{'fixture':True})
                def gpu_info(self):return {'uuid':P.EXPECTED_GPU}
                def verify_cached_unchanged(self,a):pass
                def api(self,path,body,timeout=None):
                    if path=='/apply-template':self.text='\n'.join(m['content'] for m in body['messages']);return {'prompt':self.text}
                    if path=='/tokenize':return {'tokens':[1,2,3]}
                    if path=='/completion':
                        task=re.search(r'Workload: ([\w-]+)\.',self.text)[1]
                        return {'tokens_evaluated':3,'truncated':False,'stop_type':'eos','timings':{'predicted_n':100},
                            'content':json.dumps({'block':C.SPECS[task]['base']})+'\n'+M.original(task)}
                    raise AssertionError(path)
            class Proc:
                def poll(self):return 0
            def build():
                save(ROOT/'setup/helper.so',b'fixture, not executable');return ROOT/'setup/helper.so'
            def bases(helper):jw(ROOT/'preflight/fixture.json',{'mock':True})
            def evaluate(g,records,helper):
                out=[]
                for r in records:
                    test.assertEqual(r['generation_status'],'saved')
                    out.append(r|{'correctness_passed':True,'stage':'measured','measurements':[
                       {'shape':list(s),'measurement_valid':True,'speedup':1.0,'speedup_gt_1_02':False,
                        'same_cubin':True,'same_launch_as_original':True} for s in C.SPECS[g['task']]['perf']]})
                jw(ROOT/'groups'/g['label']/'outcomes.json',out);return out
            def ack(rec):
                P.verify_archive(ROOT/'archives'/(rec['label']+'.tar.gz'),rec)
                jw(ROOT/'acks'/(rec['label']+'.json'),{'sha256':rec['sha256']})
            oldlock=P.lock
            def lock(p):return oldlock(ROOT/'fixture-exclusive.lock')
            with contextlib.ExitStack() as stack:
                for obj,name,val in [(P,'remote_guard',lambda:None),(P,'no_other_gpu',lambda:None),(P,'lock',lock),
                  (M,'probe_environment',lambda:copy.deepcopy(env)),(C,'build_helper',build),(C,'baseline_preflight',bases),
                  (C,'evaluate_group',evaluate),(C,'wait_ack',ack),(P,'module_a',lambda:Model()),
                  (P,'start_model',lambda *args:Proc()),(M,'wait_cloud',lambda r:packets[r['id']])]:
                    stack.enter_context(mock.patch.object(obj,name,val))
                with contextlib.redirect_stdout(io.StringIO()):M.worker(True)
            summary=parse(read(ROOT/'final/summary.json'))
            self.assertEqual(summary['candidate_slots'],90)
            self.assertEqual(summary['state'],'GPU004B_FIRST_TRIAL_90_COMPLETE')
            self.assertFalse(summary['prior_270_plan_complete'])
            self.assertEqual(sum(x['valid_size_measurements'] for x in summary['providers'].values()),180)
            self.assertEqual(len(list((ROOT/'receipts').glob('*.json'))),39)
            self.assertTrue((ROOT/'completion.json').exists())
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    need(result.wasSuccessful(),'Batch runner self tests failed')
    print('GPU004B_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=PINNED_CORE_COMMON_PROMPTS_BUDGET_BATCH_REPLAY_ONCE_ONLY_POSTS_AND_MOCK_GPU_ARCHIVES; NO_REAL_API_SSH_OR_A40')

# --- Additive repair for the observed pre-generation Sanitizer PATH mismatch. ---
# Original Batch, prompt, budget, API, and numerical-core functions above are unchanged.
import fcntl as _fx_fcntl
import shutil as _fx_shutil
import stat as _fx_stat
import subprocess as _fx_subprocess
import tempfile as _fx_tempfile

FIX_SCHEMA = 'gpu004b-sanitizer-absolute-path-recovery-v1'
FIX_OLD_RUNNER_SHA = '3f3e0548ecfb2be92627b3fd2ecfeb7cb63161b201e9b3b37841b30dd02f1016'
FIX_PLAN_SHA = '34d74f32290d7aef007b1e885c730253bebaa5f7b3839a04b00979a10af7511f'
FIX_SANITIZER_SHA = 'ddb2dbfd04b20e9cddf263ec9831335b92395225acf89d81cd9b3bf60476bae8'
FIX_OTHER_SANITIZER_SHA = '5cba659e1cd603aa2370e103425f184368e6ed405da90ce85743c4399c324dbc'
FIX_RESERVED = '3.610938'
FIX_ERROR = 'Environment changed since quote/plan; no generation started'
FIX_REMOTE = Path('/workspace/gpu004-batch-budget-v1')
FIX_TOOL = Path('/workspace/gpu004b-sanitizer-repair-v1/repair.py')
FIX_ARCHIVE = FIX_REMOTE.with_name(FIX_REMOTE.name + '.failed-env-before-sanitizer-pin-v1')
FIX_STAGE = FIX_REMOTE.with_name(FIX_REMOTE.name + '.prepared-sanitizer-pin-v1')
FIX_ALLOWED_OLD = {
    'control/runner.py', 'control/plan.json', 'control/authorization.json',
    'launch.json', 'progress.json', 'failure.json', 'worker.log', 'launch.lock'
}
_FIX_LEGACY_SANITIZER = P.sanitizer_path
_FIX_BATCH_MAIN = main
_FIX_BATCH_SELF_TEST = self_test


def fix_immutable(path, raw):
    """Create a file once, or require a byte-identical existing file."""
    path = P.safe(path)
    if path.exists():
        need(read(path) == raw, 'Recovery file conflict: ' + str(path))
    else:
        save(path, raw)


def fix_tree(root):
    """Bounded, no-symlink snapshot. No archived or generated program is executed."""
    root = P.safe(root)
    need(root.is_dir(), 'Missing recovery source directory: ' + str(root))
    out = {}; total = 0
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            P.safe(Path(parent) / name)
        for name in sorted(names):
            path = P.safe(Path(parent) / name)
            raw = read(path, 8 * 1024**2)
            total += len(raw)
            need(len(out) < 256 and total <= 24 * 1024**2, 'Recovery snapshot too large')
            out[path.relative_to(root).as_posix()] = raw
    return out


def fix_manifest(files):
    return {n: {'bytes': len(b), 'sha256': digest(b)} for n, b in sorted(files.items())}


def fix_validate_plan_bytes(raw):
    need(digest(raw) == FIX_PLAN_SHA, 'Not the audited plan; no automatic plan change')
    plan = parse(raw); M.validate_plan(plan)
    need(canon(plan) == raw, 'Saved plan is not canonical')
    need(plan['environment']['sanitizer_sha256'] == FIX_SANITIZER_SHA,
         'Saved plan does not pin the expected Sanitizer')
    return plan


def fix_validate_authorized(files, limit='5'):
    need(money(limit) == D('5'), 'This recovery only accepts the existing USD 5 approval')
    plan = fix_validate_plan_bytes(files['plan.json'])
    budget = parse(files['budget.json']); auth = parse(files['authorization.json'])
    M.validate_budget(plan, budget, auth)
    need(D(auth['max_api_usd']) == D('5') and auth.get('batch_only') is True,
         'Original Batch-only USD 5 authorization required')
    need(D(budget['full_cohort_reserved_usd']) == D(FIX_RESERVED), 'Original reservation differs')
    need(D(auth['full_cohort_reserved_usd']) == D(FIX_RESERVED), 'Approval reservation differs')
    rid = parse(files['run-identity.json']).get('run_id')
    need(isinstance(rid, str) and re.fullmatch(r'[0-9a-f]{12}', rid), 'Invalid original run identity')
    need(sum(len(g['requests']) for g in plan['groups']) == 90, 'Unexpected request count')
    need(plan['planned_cloud_requests'] == 60 and plan['selected_trial_numbers'] == [1],
         'Only the approved first balanced trial is allowed')
    return plan, budget, auth


def fix_local_prerequisites(root, limit='5'):
    root = P.safe(root)
    # Refuse a single intent, even when no response exists: it may already be billed.
    for sub in ('batches', 'api-ledger'):
        d = P.safe(root / sub)
        if d.exists():
            need(not fix_tree(d), 'Submission or API result record exists; use existing-run monitoring, not recovery')
    for p in root.glob('*-receipt.json'):
        raise Blocked('A checkpoint is already present; this repair is pre-generation only: ' + p.name)
    need(not (root / 'final-status.json').exists(), 'Run has already completed')
    files = {n: read(root / n) for n in ('plan.json', 'budget.json', 'authorization.json', 'run-identity.json')}
    fix_validate_authorized(files, limit)
    return files


def fix_check_old(files, local_files, *, check_alive=True):
    need(set(files).issubset(FIX_ALLOWED_OLD), 'Unexpected files in failed run; no reset performed')
    required = FIX_ALLOWED_OLD - {'launch.lock'}
    need(required.issubset(files), 'Incomplete old failure evidence; no reset performed')
    need(digest(files['control/runner.py']) == FIX_OLD_RUNNER_SHA, 'Old runner is not the audited version')
    need(files['control/plan.json'] == local_files['plan.json'], 'Remote/local frozen plan mismatch')
    need(files['control/authorization.json'] == local_files['authorization.json'], 'Remote/local approval mismatch')
    p = parse(files['progress.json']); f = parse(files['failure.json']); launch = parse(files['launch.json'])
    need(p.get('phase') == 'BLOCKED' and p.get('error') == FIX_ERROR, 'Not the audited failure')
    need(p.get('generation_calls') == 0 and p.get('evaluation_terminal') == 0, 'Experiment work already occurred')
    need(f.get('error') == 'Blocked: ' + FIX_ERROR, 'Failure record differs')
    need(launch.get('runner_sha256') == FIX_OLD_RUNNER_SHA, 'Old launch identity differs')
    if check_alive: need(not P.alive(launch), 'Old worker is still alive')
    return p


def fix_hash_executable(path, expected):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'Sanitizer path must be absolute')
    # Binding uses the existing real executable, not a copied binary or a replacement symlink.
    need(path.resolve(strict=True) == path, 'Pinned Sanitizer path changed through a symlink')
    st = path.stat()
    need(_fx_stat.S_ISREG(st.st_mode) and bool(st.st_mode & 0o111), 'Sanitizer is not executable')
    need(hfile(path) == expected, 'Pinned Sanitizer hash mismatch; no fallback')
    return str(path)


def fix_sanitizer_path():
    binding = parse(read(ROOT / 'control/sanitizer-binding.json'))
    need(binding.get('schema') == FIX_SCHEMA and binding.get('plan_sha256') == FIX_PLAN_SHA,
         'Missing/mismatched Sanitizer binding')
    plan = fix_validate_plan_bytes(read(ROOT / 'control/plan.json'))
    need(binding.get('sha256') == plan['environment']['sanitizer_sha256'] == FIX_SANITIZER_SHA,
         'Sanitizer binding does not match approved environment')
    return fix_hash_executable(binding['path'], FIX_SANITIZER_SHA)


P.sanitizer_path = fix_sanitizer_path


def fix_full_identity(observed, plan):
    expected = M.environment_identity(plan['environment'])
    actual = M.environment_identity(observed)
    changed = [k for k in expected if actual.get(k) != expected[k]]
    need(not changed, 'Environment still differs: ' + ', '.join(changed))
    return actual


def fix_version(path):
    args = [*P.unpriv_prefix(), str(path), '--version']
    cp = _fx_subprocess.run(args, env=P.clean_env(), capture_output=True, timeout=30, check=False)
    need(cp.returncode == 0, 'Pinned Sanitizer --version failed under unprivileged worker environment')
    return {'argv': args, 'returncode': cp.returncode,
            'stdout': cp.stdout.decode('utf-8', errors='replace')[:4000],
            'stderr': cp.stderr.decode('utf-8', errors='replace')[:4000]}


def fix_child_probe(where, script, plan):
    results = []
    for _ in range(2):
        cp = _fx_subprocess.run(
            ['/usr/bin/python3', '-I', '-S', '-B', str(script), '--_fixed-env-probe', str(where)],
            cwd=where, env=P.clean_env(), capture_output=True, timeout=120, check=False)
        need(cp.returncode == 0, 'Fixed worker-environment probe failed: ' +
             cp.stderr.decode('utf-8', errors='replace')[-1600:])
        observed = parse(cp.stdout); fix_full_identity(observed, plan)
        results.append(observed)
    return results


def fix_sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def fix_new_controls(raw, files, binding, old_files):
    receipt = {'schema': FIX_SCHEMA, 'plan_sha256': FIX_PLAN_SHA,
        'old_runner_sha256': FIX_OLD_RUNNER_SHA, 'new_runner_sha256': digest(raw),
        'authorization_sha256': digest(files['authorization.json']),
        'budget_sha256': digest(files['budget.json']),
        'old_files': fix_manifest(old_files), 'failed_directory': str(FIX_ARCHIVE),
        'binding': binding, 'scope': 'Restore approved Sanitizer by absolute path; preserve plan/prompt/budget and original failure',
        'provider_http_calls_in_repair': 0, 'new_generation_calls_in_repair': 0,
        'starts_worker': False}
    return {'control/runner.py': raw, 'control/plan.json': files['plan.json'],
            'control/authorization.json': files['authorization.json'],
            'control/sanitizer-binding.json': canon(binding),
            'control/sanitizer-recovery.json': canon(receipt)}


def fix_commit_stage(stage, archive, root):
    """Two same-filesystem renames. Originals stay intact in archive."""
    need(stage.is_dir() and not archive.exists(), 'Recovery destination already exists')
    root.rename(archive); fix_sync_dir(root.parent)
    stage.rename(root); fix_sync_dir(root.parent)


def fix_remote_repair(local_files):
    P.remote_guard()
    need(ROOT == FIX_REMOTE, 'Wrong experiment namespace')
    plan, budget, auth = fix_validate_authorized(local_files)
    raw = read(__file__)
    need(Path(__file__).resolve() == FIX_TOOL, 'Use the dedicated repair launcher')
    with P.lock(FIX_TOOL.parent / 'repair.lock'):
        with P.lock('/workspace/gpu-code-pilot-exclusive.lock'):
            P.no_other_gpu()
            if FIX_ARCHIVE.exists():
                old = fix_tree(FIX_ARCHIVE); fix_check_old(old, local_files)
                # Handle a disconnect between the two renames, but never rerun a worker.
                if not FIX_REMOTE.exists():
                    need(FIX_STAGE.is_dir(), 'Interrupted repair has no prepared replacement; originals retained')
                    staged = fix_tree(FIX_STAGE)
                    bind = parse(staged['control/sanitizer-binding.json'])
                    need(staged == fix_new_controls(raw, local_files, bind, old), 'Interrupted stage failed integrity check')
                    fix_hash_executable(bind['path'], FIX_SANITIZER_SHA)
                    FIX_STAGE.rename(FIX_REMOTE); fix_sync_dir(FIX_REMOTE.parent)
                active = fix_tree(FIX_REMOTE)
                need(set(active) == {'control/runner.py','control/plan.json','control/authorization.json',
                                    'control/sanitizer-binding.json','control/sanitizer-recovery.json'},
                     'Repair already launched or new evidence exists; use --watch, do not repair again')
                binding = parse(active['control/sanitizer-binding.json'])
                expected = fix_new_controls(raw, local_files, binding, old)
                need(active == expected, 'Prepared recovery artifacts changed')
                fix_hash_executable(binding['path'], FIX_SANITIZER_SHA)
                probes = fix_child_probe(FIX_REMOTE, FIX_REMOTE / 'control/runner.py', plan)
                version = fix_version(binding['path'])
            else:
                need(FIX_REMOTE.is_dir(), 'Audited failed run is missing')
                with P.lock(FIX_REMOTE / 'launch.lock'):
                    old = fix_tree(FIX_REMOTE); fix_check_old(old, local_files)
                    # Reproduce both lookup modes before selecting any file.
                    chosen = Path(_FIX_LEGACY_SANITIZER()).resolve(strict=True)
                    fix_hash_executable(chosen, FIX_SANITIZER_SHA)
                    cp = _fx_subprocess.run(['/usr/bin/python3','-I','-S','-B',
                        str(FIX_REMOTE/'control/runner.py'),'--_probe'], env=P.clean_env(), cwd=FIX_REMOTE,
                        capture_output=True, timeout=120, check=False)
                    need(cp.returncode == 0, 'Old worker-environment probe failed')
                    before = parse(cp.stdout); want = M.environment_identity(plan['environment'])
                    got = M.environment_identity(before)
                    changed = [k for k in want if got.get(k) != want[k]]
                    need(changed == ['sanitizer_sha256'] and got['sanitizer_sha256'] == FIX_OTHER_SANITIZER_SHA,
                         'Mismatch is not the audited Sanitizer-only failure; no replacement')
                    binding = {'schema': FIX_SCHEMA, 'plan_sha256': FIX_PLAN_SHA,
                        'path': str(chosen), 'sha256': FIX_SANITIZER_SHA,
                        'worker_path_lookup_before_sha256': FIX_OTHER_SANITIZER_SHA,
                        'selected_by': 'Existing SSH-environment resolver, required to match saved plan SHA-256',
                        'fallback_allowed': False}
                    version = fix_version(chosen)
                    new = fix_new_controls(raw, local_files, binding, old)
                    if FIX_STAGE.exists():
                        staged = fix_tree(FIX_STAGE)
                        need(set(staged).issubset(new) and all(new[n] == b for n,b in staged.items()),
                             'Staging conflict; nothing removed')
                    for name, content in new.items():
                        fix_immutable(FIX_STAGE / name, content)
                    for path in (FIX_STAGE, FIX_STAGE/'control'):
                        path.chmod(0o755)
                    for name in new:
                        (FIX_STAGE/name).chmod(0o444)
                    probes = fix_child_probe(FIX_STAGE, FIX_STAGE/'control/runner.py', plan)
                    need(fix_tree(FIX_REMOTE) == old, 'Old run changed during recovery')
                    need(fix_tree(FIX_STAGE) == new, 'Staging changed during verification')
                    fix_commit_stage(FIX_STAGE, FIX_ARCHIVE, FIX_REMOTE)
                    need(fix_tree(FIX_ARCHIVE) == old and fix_tree(FIX_REMOTE) == new,
                         'Post-rename integrity check failed; no worker started')
            return {'schema': FIX_SCHEMA, 'status': 'REPAIRED_NOT_STARTED',
                'plan_sha256': FIX_PLAN_SHA, 'binding': binding,
                'reserved_usd': FIX_RESERVED, 'approved_limit_usd': '5',
                'worker_clean_environment_identical_checks': len(probes),
                'new_runner_sha256': digest(raw), 'failed_directory': str(FIX_ARCHIVE),
                'failed_manifest': fix_manifest(old),
                'failed_files_b64': {n: base64.b64encode(b).decode() for n,b in old.items()},
                'version_probe': version, 'environment_probes': probes,
                'provider_http_calls': 0, 'generation_calls': 0, 'worker_started': False}


def fix_upload_text(pin):
    return '''import os,sys,hashlib
from pathlib import Path
p=Path(%r)
assert os.geteuid()==0 and Path('/workspace').is_dir(), 'Not the authorized Pod'
assert os.environ.get('RUNPOD_POD_ID',%r)==%r, 'Wrong Pod'
for q in (p,*p.parents): assert not q.is_symlink(), 'Symlink refused'
b=sys.stdin.buffer.read(1024*1024+1)
assert len(b)<=1024*1024 and hashlib.sha256(b).hexdigest()==%r, 'Upload pin mismatch'
compile(b,str(p),'exec')
p.parent.mkdir(parents=True,exist_ok=True)
if p.exists(): assert p.is_file() and p.read_bytes()==b, 'Different recovery launcher already installed'
else:
 with p.open('xb') as f: f.write(b);f.flush();os.fsync(f.fileno())
print('SANITIZER_RECOVERY_LAUNCHER_PINNED')
''' % (str(FIX_TOOL), P.POD, P.POD, pin)


def fix_store_report(dest, report, files):
    need(report.get('status') == 'REPAIRED_NOT_STARTED' and report.get('plan_sha256') == FIX_PLAN_SHA,
         'Invalid recovery receipt')
    old = {n: base64.b64decode(v, validate=True) for n,v in report['failed_files_b64'].items()}
    need(set(old).issubset(FIX_ALLOWED_OLD) and fix_manifest(old) == report['failed_manifest'], 'Bad failure backup')
    fix_check_old(old, files, check_alive=False)
    for name, content in old.items():
        fix_immutable(dest/'failed-remote'/name, content)
    for name, content in files.items():
        fix_immutable(dest/'approved-local'/name, content)
    public = {k:v for k,v in report.items() if k not in ('failed_files_b64','environment_probes')}
    # Repeated diagnosis may have different timestamps; preserve every report separately.
    saved = Path(_fx_tempfile.mkdtemp(prefix='verification-', dir=dest))
    jw(saved/'report.json', public); jw(saved/'environment-probes.json', report['environment_probes'])
    return saved/'report.json'


def fix_repair_and_run(allow, limit):
    need(os.geteuid() != 0, 'Run on WSL without sudo')
    need(allow, 'Explicit temporary-disk/local-checkpoint authorization is required')
    # Do not forward even optional preexisting cloud keys to SSH subprocesses.
    for var in ('OPENAI_API_KEY','ANTHROPIC_API_KEY'): os.environ.pop(var, None)
    root = M.local_root()
    with P.lock(root/'local-controller.lock'):
        files = fix_local_prerequisites(root, limit)
        A = P.module_a(); A.fingerprint_check(Path.home()/'.ssh/id_ed25519'); con = A.Connection()
        try:
            raw = read(__file__)
            print(con.run(['/usr/bin/python3','-I','-S','-B','-c',fix_upload_text(digest(raw))],data=raw).decode(),flush=True)
            request = canon({'files_b64': {n:base64.b64encode(b).decode() for n,b in files.items()}})
            result = parse(con.run(['/usr/bin/python3','-I','-S','-B',str(FIX_TOOL),'--_repair-sanitizer'],data=request))
            need(result['new_runner_sha256'] == digest(raw), 'Recovery runner hash mismatch')
            plan,_,_ = fix_validate_authorized(files,limit)
            for env in result['environment_probes']: fix_full_identity(env,plan)
            dest = root/'sanitizer-recovery-v1'; dest.mkdir(mode=0o700, exist_ok=True)
            rp = fix_store_report(dest, result, files)
            for n,b in files.items(): need(read(root/n) == b, 'Approved local files changed')
            fix_local_prerequisites(root,limit)
            print('SANITIZER_ABSOLUTE_PATH_PINNED=' + result['binding']['path'],flush=True)
            print('WORKER_ENVIRONMENT_MATCH=PASS checks=2',flush=True)
            print('FAILED_RUN_BACKUP_LOCAL_VERIFIED=' + str(rp),flush=True)
            print('APPROVED_PLAN_UNCHANGED='+FIX_PLAN_SHA,flush=True)
            print('RESERVED_USD_UNCHANGED='+FIX_RESERVED+'; LIMIT_USD=5',flush=True)
        finally:
            con.close()
    # Only now re-enter the original Batch controller. It reuses the immutable
    # plan/budget/approval, authenticates, starts one worker, and gates Batch POSTs
    # on passed AND locally acknowledged original CUDA controls.
    local('run', allow=True, limit='5', use_env=False)


def fix_entry():
    if '--_repair-sanitizer' in sys.argv[1:]:
        need(sys.argv[1:] == ['--_repair-sanitizer'], 'Unexpected repair arguments')
        raw = sys.stdin.buffer.read(8*1024**2+1); need(len(raw)<=8*1024**2,'Oversized recovery request')
        request = parse(raw)
        files = {n:base64.b64decode(v,validate=True) for n,v in request['files_b64'].items()}
        need(set(files) == {'plan.json','budget.json','authorization.json','run-identity.json'}, 'Unexpected local documents')
        with contextlib.redirect_stdout(sys.stderr): result = fix_remote_repair(files)
        print(json.dumps(result,ensure_ascii=False)); return
    if '--_fixed-env-probe' in sys.argv[1:]:
        need(len(sys.argv)==3 and Path(sys.argv[2]) in (FIX_STAGE,FIX_REMOTE), 'Unexpected probe target')
        configure(Path(sys.argv[2])); P.remote_guard()
        with contextlib.redirect_stdout(sys.stderr): result = M.probe_environment()
        print(json.dumps(result,ensure_ascii=False)); return
    if any(x.startswith('--_') for x in sys.argv[1:]):
        _FIX_BATCH_MAIN(); return
    ap=argparse.ArgumentParser(description='Repair the audited Sanitizer-only pre-generation failure; reuse approved Batch budget.')
    g=ap.add_mutually_exclusive_group(required=True)
    for n in ('repair-and-run','watch','collect','status','self-test','batch-core-self-test','numeric-core-self-test','auth-check','cancel-batches'):
        g.add_argument('--'+n,action='store_true')
    ap.add_argument('--api-budget-usd',default='5')
    ap.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true')
    a=ap.parse_args()
    if a.self_test: fix_self_test(); return
    if a.batch_core_self_test:
        # Legacy regression suite exercises its exact old lookup fixtures separately.
        with mock.patch.object(P,'sanitizer_path',_FIX_LEGACY_SANITIZER): _FIX_BATCH_SELF_TEST()
        return
    if a.numeric_core_self_test:
        with mock.patch.object(P,'sanitizer_path',_FIX_LEGACY_SANITIZER): C.self_test()
        return
    if a.repair_and_run: fix_repair_and_run(a.allow_ephemeral_with_local_checkpoints,a.api_budget_usd); return
    if a.cancel_batches: cancel_batches(False); return
    mode=next(n for n in ('watch','collect','status','auth_check') if getattr(a,n))
    local(mode.replace('_','-'),allow=False,limit=a.api_budget_usd,use_env=False)

FIX_ORIGINAL_PREFIX_SHA = '3e3f9df0c0b5dfaf3e6aaac85f37ebf1d369d847267a418441175481b42a6dc4'


def fix_self_test():
    import ast
    import importlib.util
    import shlex
    this = sys.modules[__name__]
    class Tests(unittest.TestCase):
        def setUp(self):
            self.tmp = _fx_tempfile.TemporaryDirectory(prefix='gpu004b-sanfix-')
            self.top = Path(self.tmp.name); self.remote = self.top/'remote'; self.remote.mkdir()
            self.localroot = self.top/'local'; self.localroot.mkdir()
            self.real_file = Path(__file__)
            self.raw = read(self.real_file)
            self.good = self.top/'good/compute-sanitizer'; self.good.parent.mkdir()
            self.bad = self.top/'bad/compute-sanitizer'; self.bad.parent.mkdir()
            self.good.write_text('#!/bin/sh\nprintf "planned-sanitizer\\n"\n'); self.good.chmod(0o755)
            self.bad.write_text('#!/bin/sh\nprintf "worker-other-sanitizer\\n"\n'); self.bad.chmod(0o755)
            env = fixture_environment(); env['sanitizer_sha256'] = hfile(self.good)
            self.plan = make_plan(cfg_document(),env); self.planraw = canon(self.plan)
            self.budget = fixture_budget(self.plan)
            self.auth = {'approved':True,'plan_sha256':digest(self.planraw),
                'budget_sha256':digest(canon(self.budget)), 'max_api_usd':'5','batch_only':True,
                'full_cohort_reserved_usd':self.budget['full_cohort_reserved_usd']}
            self.files = {'plan.json': self.planraw,'budget.json':canon(self.budget),
                'authorization.json':canon(self.auth),'run-identity.json':canon({'run_id':'123456789abc'})}
            self.stack = contextlib.ExitStack()
            self.previous_root = ROOT
            for name,value in [('FIX_PLAN_SHA',digest(self.planraw)),('FIX_SANITIZER_SHA',hfile(self.good)),
                ('FIX_OTHER_SANITIZER_SHA',hfile(self.bad)),('FIX_RESERVED',self.budget['full_cohort_reserved_usd']),
                ('FIX_REMOTE',self.remote),('FIX_ARCHIVE',self.top/'failed'),('FIX_STAGE',self.top/'prepared'),
                ('FIX_TOOL',self.top/'tools/repair.py')]:
                self.stack.enter_context(mock.patch.object(this,name,value))
            configure(self.remote)
            self.binding = {'schema':FIX_SCHEMA,'plan_sha256':FIX_PLAN_SHA,'path':str(self.good),
                'sha256':FIX_SANITIZER_SHA,'worker_path_lookup_before_sha256':FIX_OTHER_SANITIZER_SHA,
                'selected_by':'Existing SSH-environment resolver, required to match saved plan SHA-256','fallback_allowed':False}
            self.oldraw=b'# original failed runner fixture\n'
            self.stack.enter_context(mock.patch.object(this,'FIX_OLD_RUNNER_SHA',digest(self.oldraw)))
            self.old={'control/runner.py':self.oldraw,'control/plan.json':self.planraw,
                'control/authorization.json':self.files['authorization.json'],
                'launch.json':canon({'pid':99999999,'ticks':'000','runner_sha256':FIX_OLD_RUNNER_SHA}),
                'progress.json':canon({'phase':'BLOCKED','error':FIX_ERROR,'generation_calls':0,'evaluation_terminal':0}),
                'failure.json':canon({'error':'Blocked: '+FIX_ERROR,'utc':'fixture'}),
                'worker.log':b'ENVIRONMENT_CHECK_FAILED\n','launch.lock':b''}
        def tearDown(self):
            self.stack.close(); configure(self.previous_root); self.tmp.cleanup()
        def install_old(self):
            for n,b in self.old.items(): fix_immutable(self.remote/n,b)
            for n,b in self.files.items(): fix_immutable(self.localroot/n,b)
            fix_immutable(FIX_TOOL,self.raw)
        def install_binding(self):
            fix_immutable(self.remote/'control/plan.json',self.planraw)
            fix_immutable(self.remote/'control/sanitizer-binding.json',canon(self.binding))
        def call_remote(self, interrupt=False):
            real_lock=P.lock
            def safe_lock(path):
                return real_lock(self.top/'exclusive.lock' if str(path)=='/workspace/gpu-code-pilot-exclusive.lock' else path)
            before=copy.deepcopy(self.plan['environment']);before['sanitizer_sha256']=FIX_OTHER_SANITIZER_SHA
            def oldprobe(argv,**kwargs):
                self.assertEqual(argv[-1],'--_probe')
                return _fx_subprocess.CompletedProcess(argv,0,canon(before),b'')
            real_commit=fix_commit_stage
            def broken_commit(stage,archive,root):
                root.rename(archive);raise OSError('simulated disconnect between renames')
            with contextlib.ExitStack() as st:
                for obj,name,value in [(this,'__file__',str(FIX_TOOL)),(P,'remote_guard',lambda:None),
                    (P,'no_other_gpu',lambda:None),(P,'lock',safe_lock),
                    (this,'_FIX_LEGACY_SANITIZER',lambda:str(self.good)),
                    (this,'fix_version',lambda p:{'returncode':0,'stdout':'planned tool fixture'}),
                    (this,'fix_child_probe',lambda *a:[copy.deepcopy(self.plan['environment'])]*2),
                    (_fx_subprocess,'run',oldprobe)]:st.enter_context(mock.patch.object(obj,name,value))
                if interrupt:st.enter_context(mock.patch.object(this,'fix_commit_stage',broken_commit))
                return fix_remote_repair(self.files)
        def test_approved_plan_and_reservation_valid(self):
            fix_validate_authorized(self.files)
        def test_raise_limit_refused(self):
            with self.assertRaises(Blocked):fix_validate_authorized(self.files,'6')
        def test_plan_tamper_refused(self):
            f=dict(self.files);f['plan.json']=self.planraw+b' '
            with self.assertRaises(Blocked):fix_validate_authorized(f)
        def test_budget_tamper_refused(self):
            f=dict(self.files);b=dict(self.budget);b['full_cohort_reserved_usd']='0.1';f['budget.json']=canon(b)
            with self.assertRaises(Blocked):fix_validate_authorized(f)
        def test_nonbatch_approval_refused(self):
            f=dict(self.files);a=dict(self.auth);a['batch_only']=False;f['authorization.json']=canon(a)
            with self.assertRaises(Blocked):fix_validate_authorized(f)
        def test_missing_authorization_refused(self):
            f=dict(self.files);a=dict(self.auth);a['approved']=False;f['authorization.json']=canon(a)
            with self.assertRaises(Blocked):fix_validate_authorized(f)
        def test_local_no_submission(self):
            self.install_old(); self.assertEqual(fix_local_prerequisites(self.localroot),self.files)
        def test_local_uncertain_intent_refused(self):
            self.install_old();fix_immutable(self.localroot/'batches/openai/submission-intent.json',b'{}')
            with self.assertRaises(Blocked):fix_local_prerequisites(self.localroot)
        def test_local_receipt_refused(self):
            self.install_old();fix_immutable(self.localroot/'batches/anthropic/submission-response.json',b'{}')
            with self.assertRaises(Blocked):fix_local_prerequisites(self.localroot)
        def test_local_api_ledger_refused(self):
            self.install_old();fix_immutable(self.localroot/'api-ledger/task/package.json',b'{}')
            with self.assertRaises(Blocked):fix_local_prerequisites(self.localroot)
        def test_local_checkpoint_refused(self):
            self.install_old();fix_immutable(self.localroot/'original-controls-receipt.json',b'{}')
            with self.assertRaises(Blocked):fix_local_prerequisites(self.localroot)
        def test_zero_work_evidence(self):
            fix_check_old(self.old,self.files)
        def test_any_generation_refused(self):
            old=dict(self.old);p=parse(old['progress.json']);p['generation_calls']=1;old['progress.json']=canon(p)
            with self.assertRaises(Blocked):fix_check_old(old,self.files)
        def test_any_evaluation_refused(self):
            old=dict(self.old);p=parse(old['progress.json']);p['evaluation_terminal']=1;old['progress.json']=canon(p)
            with self.assertRaises(Blocked):fix_check_old(old,self.files)
        def test_active_worker_refused(self):
            with mock.patch.object(P,'alive',return_value=True):
                with self.assertRaises(Blocked):fix_check_old(self.old,self.files)
        def test_unknown_remote_file_refused(self):
            old=dict(self.old);old['groups/test/candidate.cu']=b'x'
            with self.assertRaises(Blocked):fix_check_old(old,self.files)
        def test_wrong_failure_refused(self):
            old=dict(self.old);old['failure.json']=canon({'error':'GPU execution failed'})
            with self.assertRaises(Blocked):fix_check_old(old,self.files)
        def test_wrong_runner_refused(self):
            old=dict(self.old);old['control/runner.py']=b'new'
            with self.assertRaises(Blocked):fix_check_old(old,self.files)
        def test_missing_binding_refused(self):
            with self.assertRaises(OSError):fix_sanitizer_path()
        def test_binding_matches_plan(self):
            self.install_binding();self.assertEqual(fix_sanitizer_path(),str(self.good))
        def test_no_path_fallback(self):
            self.install_binding();self.good.write_text('modified')
            with mock.patch.dict(os.environ,{'PATH':str(self.bad.parent)}):
                with self.assertRaises(Blocked):fix_sanitizer_path()
        def test_wrong_binding_plan_refused(self):
            b=dict(self.binding);b['plan_sha256']='0'*64
            fix_immutable(self.remote/'control/sanitizer-binding.json',canon(b))
            with self.assertRaises(Blocked):fix_sanitizer_path()
        def test_pinned_symlink_replacement_refused(self):
            self.install_binding();self.good.unlink();self.good.symlink_to(self.bad)
            with self.assertRaises(Blocked):fix_sanitizer_path()
        def test_unexecutable_refused(self):
            self.good.chmod(0o644)
            with self.assertRaises(Blocked):fix_hash_executable(self.good,FIX_SANITIZER_SHA)
        def test_relative_path_refused(self):
            with self.assertRaises(Blocked):fix_hash_executable('compute-sanitizer',FIX_SANITIZER_SHA)
        def test_environment_sanitizer_mismatch_not_ignored(self):
            e=copy.deepcopy(self.plan['environment']);e['sanitizer_sha256']=FIX_OTHER_SANITIZER_SHA
            with self.assertRaises(Blocked):fix_full_identity(e,self.plan)
        def test_other_environment_changes_not_ignored(self):
            for field,value in [('gpu_uuid','bad'),('driver_version','bad'),('nvrtc_sha256','bad'),('host_compiler','bad')]:
                e=copy.deepcopy(self.plan['environment']);e[field]=value
                with self.subTest(field=field):
                    with self.assertRaises(Blocked):fix_full_identity(e,self.plan)
        def test_observational_fields_not_identity(self):
            e=copy.deepcopy(self.plan['environment']);e['observed_utc']='new';e['free_disk_bytes']=123
            fix_full_identity(e,self.plan)
        def test_file_create_once(self):
            p=self.top/'once';fix_immutable(p,b'x');fix_immutable(p,b'x')
            with self.assertRaises(Blocked):fix_immutable(p,b'y')
            self.assertEqual(read(p),b'x')
        def test_tree_symlink_refused(self):
            (self.remote/'bad').symlink_to(self.good)
            with self.assertRaises(Blocked):fix_tree(self.remote)
        def test_transaction_preserves_old_bytes(self):
            self.install_old();r=self.call_remote()
            self.assertEqual(fix_tree(FIX_ARCHIVE),self.old)
            self.assertEqual(r['provider_http_calls'],0);self.assertEqual(r['generation_calls'],0)
            self.assertFalse((FIX_REMOTE/'launch.json').exists())
            self.assertEqual(read(FIX_REMOTE/'control/plan.json'),self.planraw)
            self.assertEqual(read(FIX_REMOTE/'control/authorization.json'),self.files['authorization.json'])
            self.assertEqual(fix_sanitizer_path(),str(self.good))
        def test_prelaunch_reentry_is_idempotent(self):
            self.install_old();a=self.call_remote();snap=fix_tree(FIX_REMOTE);b=self.call_remote()
            self.assertEqual(fix_tree(FIX_REMOTE),snap);self.assertEqual(a['failed_manifest'],b['failed_manifest'])
        def test_recovery_interrupted_between_renames(self):
            self.install_old()
            with self.assertRaises(OSError):self.call_remote(interrupt=True)
            self.assertFalse(FIX_REMOTE.exists());self.assertTrue(FIX_ARCHIVE.exists())
            self.call_remote();self.assertEqual(fix_tree(FIX_ARCHIVE),self.old)
        def test_reentry_after_launch_refused(self):
            self.install_old();self.call_remote();fix_immutable(FIX_REMOTE/'launch.json',b'{}')
            with self.assertRaises(Blocked):self.call_remote()
        def test_existing_archive_tamper_refused(self):
            self.install_old();self.call_remote();(FIX_ARCHIVE/'worker.log').write_bytes(b'changed')
            with self.assertRaises(Blocked):self.call_remote()
        def test_stage_conflict_does_not_touch_old(self):
            self.install_old();fix_immutable(FIX_STAGE/'unexpected',b'x')
            with self.assertRaises(Blocked):self.call_remote()
            self.assertEqual(fix_tree(FIX_REMOTE),self.old)
        def test_failed_clean_probe_does_not_touch_old(self):
            self.install_old()
            # Simulate the probe helper itself refusing an unrelated environment change.
            with mock.patch.object(this,'fix_full_identity',side_effect=Blocked('other difference')):
                with self.assertRaises(Blocked):fix_child_probe(self.remote,self.real_file,self.plan)
            self.assertEqual(fix_tree(FIX_REMOTE),self.old)
        def test_local_failure_backup_byte_exact(self):
            self.install_old();r=self.call_remote();dest=self.top/'backup';dest.mkdir()
            fix_store_report(dest,r,self.files)
            self.assertEqual(fix_tree(dest/'failed-remote'),self.old)
            self.assertEqual(fix_tree(dest/'approved-local'),self.files)
        def test_failure_backup_tamper_refused(self):
            self.install_old();r=self.call_remote();r['failed_files_b64']['worker.log']=base64.b64encode(b'changed').decode()
            dest=self.top/'backup';dest.mkdir()
            with self.assertRaises(Blocked):fix_store_report(dest,r,self.files)
        def test_original_logic_prefix_is_unchanged(self):
            original_prefix=self.raw.split(b'\n# --- Additive repair',1)[0]
            self.assertEqual(digest(original_prefix),FIX_ORIGINAL_PREFIX_SHA)
            self.assertEqual(digest(BASE_RAW),BASE_SHA)
            self.assertEqual(M.CORE_SHA,'afe6858e7d510084a40e97aa81c14fa9da907fc80bc23f4a8b76f1eccf14e90a')
        def test_batch_only_and_once_guards_still_present(self):
            self.assertTrue(allowed_http('openai','POST','/v1/batches'))
            self.assertTrue(allowed_http('anthropic','POST','/v1/messages/batches'))
            self.assertFalse(allowed_http('openai','POST','/v1/responses'))
            self.assertFalse(allowed_http('anthropic','POST','/v1/messages'))
            self.assertEqual(len(provider_requests(self.plan,'openai')),30)
            self.assertEqual(len(provider_requests(self.plan,'anthropic')),30)
        def test_same_paid_payloads_and_90_prompts(self):
            self.assertEqual(len(M.index_requests(self.plan)),90)
            fix_validate_authorized(self.files)
            for provider in CLOUD:
                a,b=batch_input(self.plan,provider,'123456789abc')
                self.assertEqual(len(b),30)
                self.assertNotIn(b'compute-sanitizer',a)
        def test_repair_has_no_provider_or_generation_calls(self):
            t=ast.parse(self.raw.decode());wanted={
                'fix_remote_repair','fix_child_probe','fix_version','fix_commit_stage','fix_sanitizer_path'}
            for n in t.body:
                if isinstance(n,ast.FunctionDef) and n.name in wanted:
                    calls=[c.func.id for c in ast.walk(n) if isinstance(c,ast.Call) and isinstance(c.func,ast.Name)]
                    self.assertFalse(set(calls)&{'http_request','api_http','submit_once','process_batches','generate_group'})
        def test_upload_is_pinned_and_has_no_cloud_key(self):
            s=fix_upload_text(digest(self.raw));compile(s,'upload','exec')
            self.assertIn(str(FIX_TOOL),s);self.assertIn(digest(self.raw),s)
            self.assertNotIn('OPENAI_API_KEY',s);self.assertNotIn('ANTHROPIC_API_KEY',s)
        def test_real_subprocess_path_mismatch_then_pin(self):
            self.install_binding()
            # Run the actual new resolver in a clean child; substitute only fixture pins/root.
            program='''import importlib.util,sys,os,json
from pathlib import Path
p=sys.argv[1]
s=importlib.util.spec_from_file_location('recovery_fixture',p)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
m.configure(Path(sys.argv[2]));m.FIX_PLAN_SHA=sys.argv[3];m.FIX_SANITIZER_SHA=sys.argv[4]
m.M.validate_plan=lambda plan:None
print(json.dumps({'legacy':str(Path(m._FIX_LEGACY_SANITIZER()).resolve()),'pinned':m.fix_sanitizer_path()}))
'''
            env={'PATH':str(self.bad.parent),'HOME':str(self.top),'LANG':'C'}
            cp=_fx_subprocess.run([sys.executable,'-I','-S','-B','-c',program,str(self.real_file),str(self.remote),
                 FIX_PLAN_SHA,FIX_SANITIZER_SHA],env=env,capture_output=True,timeout=30)
            self.assertEqual(cp.returncode,0,cp.stderr.decode());obj=parse(cp.stdout)
            self.assertEqual(obj['legacy'],str(self.bad));self.assertEqual(obj['pinned'],str(self.good))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    need(result.wasSuccessful(),'Sanitizer recovery self tests failed')
    print('GPU004B_SANITIZER_FIX_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=LOCAL_PINS_REAL_CHILD_PATH_SELECTION_FILESYSTEM_RECOVERY_AND_BATCH_GUARDS; NO_REAL_SSH_API_CUDA_OR_GPU')

if __name__ == '__main__':
    try:
        fix_entry()
    except (Blocked,ValueError,OSError,http.client.HTTPException,KeyError) as exc:
        print('GPU004B_SANITIZER_RECOVERY_BLOCKED: '+str(exc),file=sys.stderr)
        print('Evidence retained. No environment-check bypass, paid resubmission, old-result deletion, or Pod termination.',file=sys.stderr)
        sys.exit(2)
