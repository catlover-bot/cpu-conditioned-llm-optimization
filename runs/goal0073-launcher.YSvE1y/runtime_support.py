"""Generation orchestration for corrected resource budgets.
Uses the frozen validator unchanged. Each failed request is terminal; restart
only the owned inference server after transport failure, never the request.
"""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import time
import uuid
from streaming_support import receive


def request_limit(item):
    return 1800 if item['form'] == 'C' else 7200


def can_start(item, now, deadline):
    # Do not begin a request unless its full declared budget fits.
    return now + request_limit(item) + 45 <= deadline


def generation_phase(b, pkg, plan, run, deadline, freeze, binary):
    service = None
    consecutive_transport_failures = 0
    def ensure_stopped():
        nonlocal service
        b.stop(service)
        service = None
        b.check_busy()  # Any surviving/foreign inference blocks further work.

    def ensure_service():
        nonlocal service
        if service is not None:
            b.need(service.poll() is None, '推論サービスが異常終了しました')
            return
        b.check_busy()
        with socket.socket() as s:
            b.need(s.connect_ex(('127.0.0.1', b.SERVICE_PORT)) != 0,
                   '既存サービスのポートを置き換えません')
        logpath = run/'sessions'/('ollama-stream-'+uuid.uuid4().hex[:8]+'.log')
        with logpath.open('xb') as log:
            service = subprocess.Popen(b.model_command(binary), env=b.env(),
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                start_new_session=True)
        for _ in range(120):
            b.need(service.poll() is None, 'Ollama起動失敗')
            try:
                _, obj = b.api('/api/version', timeout=2)
                b.need(obj.get('version') == '0.33.3', 'Ollamaの版不一致')
                break
            except (ConnectionError, TimeoutError, OSError):
                time.sleep(.5)
        else:
            raise b.Blocked('Ollamaに接続できません')
        _, tags = b.api('/api/tags')
        matches = [x for x in tags.get('models', [])
                   if x.get('name', x.get('model')) == b.MODEL]
        b.need(len(matches) == 1 and matches[0]['digest'].removeprefix('sha256:')
               == freeze['manifest_sha256'], 'APIのモデルハッシュ不一致')
        _, show = b.api('/api/show', {'model': b.MODEL})
        b.need(not show.get('remote_host') and not show.get('remote_model'),
               'クラウドモデルを拒否')
        b.need(show.get('model_info', {}).get('qwen2.context_length', 0) >= b.CTX,
               '文脈長未対応')

    def heartbeat(item, d, status):
        rec = {'request_id': item['id'], 'utc': b.now(), **status}
        b.atomic(d/'live-progress.json', rec)
        b.atomic(run/'live-generation.json', rec)
        print('  受信中:', item['id'],
              f"{status['elapsed_seconds']/60:.1f}分",
              '断片数=', status['received_json_records'],
              '保存bytes=', status['partial_text_bytes'], flush=True)

    try:
        for index, item in enumerate(plan['tasks'], 1):
            d = run/'generation'/item['id']
            if (d/'result.json').is_file():
                continue
            # Retain ambiguous prior attempts; never resend after interruption.
            response = d/'response.raw.json'
            if (d/'started.json').exists() and not response.exists():
                b.jw(d/'result.json', {'status':'interrupted_unknown_response',
                    'automatic_retry':False,'utc':b.now(),
                    'partial_stream_retained':(d/'response.stream.jsonl').exists()})
                b.atomic(run/'progress.json', b.results_summary(plan,run))
                continue
            b.need(item['context_budget_ok'] is True, '新計画の入出力予算不一致')
            if not response.exists():
                if not can_start(item, time.monotonic(), deadline):
                    print('時間枠不足のため新要求を開始せず、保存済み分の検証へ移ります。', flush=True)
                    break
                ensure_service()
                # Startup time must also fit the complete per-request budget.
                if not can_start(item, time.monotonic(), deadline):
                    break
                d.mkdir(parents=True, exist_ok=True)
                payload = b.load(b.safe(pkg,item['request']))
                b.need(b.sha(pkg/item['request'])==item['request_sha256'],'要求改変')
                b.need(payload['stream'] is True and payload['options']['num_predict']==b.CAPS[item['form']], '生成予算が不一致')
                b.jw(d/'request.json', payload)
                b.jw(d/'started.json', {'utc':b.now(),'request_sha256':item['request_sha256'],
                    'model_digest':freeze['manifest_sha256'],
                    'resource_policy':plan['revision'], 'timeout_seconds':request_limit(item)})
                print(f'生成 {index}/{len(plan["tasks"])} {item["task"]}/{item["size"]}/{item["form"]}（途中出力を保存）', flush=True)
                try:
                    obj, transport = receive(payload,d,request_limit(item),
                        heartbeat=lambda x:heartbeat(item,d,x))
                    # This reconstructed object is kept for the existing validator;
                    # raw wire bytes are response.stream.jsonl, never overwritten.
                    b.jw(response,obj)
                    b.jw(d/'transport-receipt.json',transport)
                    consecutive_transport_failures = 0
                except b.BudgetPause:
                    b.jw(d/'result.json',{'status':'session_resource_timeout',
                        'automatic_retry':False,'utc':b.now(),
                        'partial_stream_retained':True})
                    raise
                except Exception as exc:
                    b.jw(d/'result.json', {'status':'generation_transport_failure',
                        'error':type(exc).__name__+':'+str(exc),
                        'automatic_retry':False,'utc':b.now(),
                        'partial_stream_retained':(d/'response.stream.jsonl').exists()})
                    b.atomic(run/'progress.json',b.results_summary(plan,run))
                    consecutive_transport_failures += 1
                    ensure_stopped()
                    if consecutive_transport_failures >= 2:
                        print('連続2件の通信/時間失敗。費用保護のため生成を止め、既存分の検証へ移ります。',flush=True)
                        break
                    print('この要求は失敗記録を保持。再送せず、次の未送信要求へ進みます。',flush=True)
                    continue
            else:
                obj = b.load(response)
            # Count mismatch is an acquisition problem; save and stop, not mass-send.
            if obj.get('prompt_eval_count') != item['reference_tokenizer_input_tokens']:
                b.jw(d/'result.json',{'status':'input_count_mismatch',
                    'observed':obj.get('prompt_eval_count'),
                    'expected':item['reference_tokenizer_input_tokens'],
                    'automatic_retry':False,'utc':b.now()})
                raise b.Blocked('公式トークナイザーと実応答の入力数が不一致')
            try:
                code, receipt = b.extract_response(obj,item)
                receipt.update({'response_reconstructed_from_stream':True,
                    'resource_policy':plan['revision'],
                    'load_duration_ns':obj.get('load_duration'),
                    'prompt_eval_duration_ns':obj.get('prompt_eval_duration'),
                    'eval_duration_ns':obj.get('eval_duration')})
                dest = d/('candidate.c' if item['form']=='C' else 'candidate.ll')
                if dest.exists(): b.need(dest.read_text()==code,'既存コードとの不一致')
                else: b.write(dest,code)
                b.jw(d/'result.json',{'status':'saved','code_sha256':b.sha(dest),
                    'receipt':receipt,'utc':b.now()})
                print('  保存済み（未検証） 出力=',receipt['output_tokens'],flush=True)
            except Exception as exc:
                b.jw(d/'result.json',{'status':'invalid_generation',
                    'error':type(exc).__name__+':'+str(exc),
                    'automatic_retry':False,'utc':b.now()})
            b.atomic(run/'progress.json',b.results_summary(plan,run))
    finally:
        b.stop(service)
    b.check_busy()
    print('自分が起動した推論サービス停止済み。共通検証・暫定計測へ移ります。',flush=True)
