# Scheduling-only adapter. All validators, inference settings and requests are unchanged.
def run_pipeline_until_complete(pkg):
    pkg=Path(pkg).resolve();host_guard();clang,version=clang_path()
    hashes=hm(pkg)
    for rel,h in hashes.items():need(sha(safe(pkg,rel))==h,'転送パッケージが改変されています: '+rel)
    plan=load(pkg/'plan.json');need(plan.get('revision')==REV and plan['requests']==len(plan['tasks']) and 0<len(plan['tasks'])<=180,'実行計画不一致')
    run=pkg.parent/'results';run.mkdir(exist_ok=True);(run/'sessions').mkdir(exist_ok=True)
    lock=open('/var/lock/cpucond-batch-codegen.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.monotonic();gen_end=math.inf
    def budget_signal(signum,frame):raise BudgetPause('外部から停止要求')
    signal.signal(signal.SIGTERM,budget_signal)
    session=run/'sessions'/('session-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.json')
    record={'started_utc':now(),'phase':'preflight','max_hours':None,'generation_hours':None,
       'orchestration_revision':'completion-driven-v1','aggregate_time_limit_seconds':None,
       'termination_condition':'all_planned_attempts_validations_and_eligible_measurements_terminal',
       'plan_sha256':sha(pkg/'plan.json'),'compiler':version,'hostname':socket.gethostname(),'errors':[]}
    box=None
    try:
        with open(run/'frozen-plan-sha256','a+') as f:
            f.seek(0);old=f.read().strip()
            if old:need(old==sha(pkg/'plan.json'),'再開する計画が変更されています')
            else:f.write(sha(pkg/'plan.json')+'\n')
        box=Sandbox(run/'sandbox-records'/uuid.uuid4().hex[:8],None);box.preflight()
        account,binary,freeze,blobs=model_state();record['model_freeze']=freeze;record['model_blobs']=blobs
        if (run/'frozen-model.json').exists():need(load(run/'frozen-model.json')==freeze,'再開時モデルが変化')
        else:jw(run/'frozen-model.json',freeze)
        frozen_host={'machine_id':Path('/etc/machine-id').read_text().strip(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'kernel_release':os.uname().release,'compiler':version,'compiler_binary_sha256':sha(Path(clang).resolve())}
        if (run/'frozen-host.json').exists():need(load(run/'frozen-host.json')==frozen_host,'再開先の実機/OS/コンパイラが変化。自動で旧計測を混ぜません')
        else:jw(run/'frozen-host.json',frozen_host)
        atomic(run/'progress.json',results_summary(plan,run))
        if results_summary(plan,run)['requests_pending']:
            record['phase']='generation';generation_phase(pkg,plan,run,gen_end,freeze,binary)
        # 他の推論サービスが残る場合は計測しない。
        check_busy();host_guard()
        record['phase']='validation_and_measurement'
        for item in plan['tasks']:
            gen=run/'generation'/item['id']/'result.json'
            if not gen.exists():continue
            if (run/'validation'/item['id']/'result.json').exists():
                v=load(run/'validation'/item['id']/'result.json')
                if (run/'measurement'/item['id']/'result.json').exists() or not v.get('measurement_eligible_provisional'):continue
            inst=next(x for x in plan['instances_list'] if (x['task'],x['size'])==(item['task'],item['size']))
            print('検証:',item['id'],flush=True)
            gr=load(gen)
            if gr['status']!='saved':
                vd=run/'validation'/item['id'];vd.mkdir(parents=True,exist_ok=True)
                if not (vd/'result.json').exists():jw(vd/'result.json',{'id':item['id'],'status':'generation_failed','official_all_passed':False,'multiinput_status':'not_run','measurement_eligible_provisional':False})
                continue
            base=prepare_baseline(box,clang,pkg,inst,run)
            v=validate_candidate(box,clang,pkg,plan,run,item,inst,base)
            print('  公式入力=',v['official_all_passed'],'追加検証=',v['multiinput_status'],flush=True)
            if v.get('measurement_eligible_provisional'):
                z=measurement(box,clang,run,inst,item,base,v)
                print('  暫定速度倍率=',z.get('speedup'),'計測品質=',z['measurement_valid'],flush=True)
            atomic(run/'progress.json',results_summary(plan,run))
        final_counts=results_summary(plan,run)
        if final_counts['requests_pending']:
            raise Blocked('連続した通信/時間失敗などで生成が停止しました。総時間制限ではありません。失敗した要求を自動再送しません。')
        need(final_counts['validation_terminal']==len(plan['tasks']) and final_counts['measurement_pending']==0,'検証/計測が未完了です。完了扱いにしません')
        record['phase']='completed'
    except BudgetPause:
        record['phase']='external_stop'
    except Exception as exc:
        record['phase']='blocked';record['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        if box:box.close()
        summary=results_summary(plan,run);summary['current_session']=record;summary['run_directory']=str(run)
        summary['active_orchestration']={'revision':'completion-driven-v1','session_limit_seconds':None,'generation_window_seconds':None,'original_plan_time_settings_superseded_for_orchestration_only':True}
        summary['completion']='DATASET_BATCH_COMPLETE' if summary['generation_terminal']==len(plan['tasks']) and summary['validation_terminal']==len(plan['tasks']) and summary['measurement_pending']==0 and record['phase']!='blocked' else ('DATASET_BATCH_BLOCKED' if record['phase']=='blocked' else 'DATASET_BATCH_PAUSED')
        summary['completion_means_all_requested_attempts_processed_not_all_correct']=True
        record['finished_utc']=now();record['elapsed_seconds']=time.monotonic()-start
        jw(session,record);atomic(run/'summary.json',summary);atomic(run/'progress.json',summary)
        # セッション単位の結果ハッシュ一覧。前の一覧を上書きしない。
        receipt=run/'sessions'/(session.stem+'-hashes.txt')
        write(receipt,''.join(f'{sha(p)}  {p.relative_to(run).as_posix()}\n' for p in sorted(run.rglob('*')) if p.is_file() and not p.is_symlink()))
        print('\n=== データセット一括実行結果 ===\n'+json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
        print(summary['completion'],flush=True)
        print('保存先:',run,flush=True)
    lock.close()
    return 1 if record['errors'] or record['phase']=='external_stop' else 0
