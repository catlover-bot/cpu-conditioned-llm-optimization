#!/usr/bin/env python3
from __future__ import annotations
import argparse, fcntl, hashlib, importlib.util, json, os, re, socket, tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

EXPECTED_CLAUDE_SHA="671dcea8f9e1c34d5548e7a8f1b8a6b3cad4508bdadcb2be6da3a4fd84b6f41f"
EXPECTED_EVIDENCE_SHA="398c2af1dff04a390613f209fcdde99022ec251464a798742bc0cd2d4ec09c79"
EXPECTED_VALIDATOR_SHA="81dae012bfba1c7ebe2db583f3813dd96a828acdf540c701c733d1c4aeaf3f53"
EXPECTED_STAGE9_RESULTS_SHA="24e07afbf84f431419fe6101b7f637ce4c840b16f4ab3655104a7dacca1e3266"
EXPECTED_STAGE9_LEDGER_SHA="aef2fc5f81292b7aaa52ef56e76b16f156d65ee9a51f256aae121f1182d3bc0c"
EXPECTED_TRANSFER_MANIFEST_SHA="8d6d11637fa0ccdec92267fbb0f89a432a8e2b31af1cbbd6eb1293a096d27551"
ID_RE=re.compile(r"^(?P<task>.+)__(?P<size>MINI|SMALL|MEDIUM)__(?P<form>C|IR)__(?P<condition>P0|P1|P2)__s(?P<sample>[0-9]+)$")

def need(x,m):
    if not x: raise RuntimeError(m)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""): h.update(b)
    return h.hexdigest()

def cj(x):
    return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]

def atomic(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+".tmp"); q.write_bytes(cj(x)); os.replace(q,p)

def pid(cid):
    m=ID_RE.fullmatch(cid); need(m is not None,"bad custom_id: "+cid)
    d=m.groupdict(); d["sample"]=int(d["sample"]); return d

def safe_extract_claude(archive,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    root="claude-sonnet5-server-transfer-v1"; seen=set()
    with tarfile.open(archive,"r:gz") as tf:
        for ti in tf:
            pp=PurePosixPath(ti.name)
            need(not pp.is_absolute() and ".." not in pp.parts,"unsafe tar path")
            need(pp.parts and pp.parts[0]==root,"unexpected archive root")
            if ti.isdir(): continue
            need(ti.isfile() and not ti.issym() and not ti.islnk(),"non-regular tar member")
            need(ti.size<=64*1024*1024,"oversize tar member")
            rel=PurePosixPath(*pp.parts[1:]).as_posix()
            need(rel and rel not in seen,"duplicate archive member"); seen.add(rel)
            f=tf.extractfile(ti); need(f is not None,"tar read failed")
            data=f.read(64*1024*1024+1); need(len(data)==ti.size,"tar size mismatch")
            dest=out/Path(*PurePosixPath(rel).parts); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
    need(sha(out/"manifest.json")==EXPECTED_TRANSFER_MANIFEST_SHA,"transfer manifest SHA mismatch")
    sums={}
    for line in (out/"SHA256SUMS").read_text().splitlines():
        h,sep,n=line.partition("  "); need(sep and re.fullmatch(r"[0-9a-f]{64}",h),"bad SHA256SUMS")
        need(n not in sums,"duplicate SHA entry"); sums[n]=h
    for n,h in sums.items():
        p=out/Path(*PurePosixPath(n).parts)
        need(p.is_file() and sha(p)==h,"internal transfer hash mismatch: "+n)
    need(sha(out/"results.jsonl")==EXPECTED_STAGE9_RESULTS_SHA,"Stage9 results mismatch")
    need(sha(out/"generation_ledger.jsonl")==EXPECTED_STAGE9_LEDGER_SHA,"Stage9 ledger mismatch")
    return out

def load_validator(path):
    need(sha(path)==EXPECTED_VALIDATOR_SHA,"goal0079 validator SHA mismatch")
    spec=importlib.util.spec_from_file_location("goal0079_frozen",path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    need(getattr(m,"REV",None)=="all30-custom-fullstate-revalidation-v1.1","validator revision mismatch")
    return m

def result_path(out,cid):
    return Path(out)/"results"/pid(cid)["condition"]/cid/"result.json"

def generation_failure(row,out):
    cid=row["custom_id"]; p=pid(cid); dest=result_path(out,cid)
    if dest.exists(): return load(dest)
    r={"id":cid,"condition":p["condition"],"task":p["task"],"size":p["size"],"form":p["form"],
       "status":"generation_failed","passed":False,"errors":row.get("errors") or [],
       "source_stage":"claude_stage9","candidate_executed":False}
    atomic(dest,r); return r

def run(args):
    evidence=Path(args.evidence).resolve(); claude=Path(args.claude).resolve()
    validator=Path(args.validator).resolve(); out=Path(args.out).resolve()
    need(sha(evidence)==EXPECTED_EVIDENCE_SHA,"evidence SHA mismatch")
    need(sha(claude)==EXPECTED_CLAUDE_SHA,"Claude archive SHA mismatch")
    need(os.geteuid()==0,"run as root for bwrap sandbox")
    need(socket.gethostname()=="cpucond-zen2-01","wrong host: "+socket.gethostname())
    need("AMD EPYC 7402" in Path("/proc/cpuinfo").read_text(),"wrong CPU")
    m=load_validator(validator); clang,ver=m.clang18()
    out.mkdir(parents=True,exist_ok=True)

    with open("/run/lock/cpucond-claude-stage11.lock","a") as lk:
        try: fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError("another Stage-11 validation is running")

        state={"revision":"claude-sonnet5-zen2-fullstate-validation-v1","completion":"RUNNING",
               "hostname":socket.gethostname(),"cpu":args.cpu,"node":args.node,
               "validator_sha256":EXPECTED_VALIDATOR_SHA,"evidence_sha256":EXPECTED_EVIDENCE_SHA,
               "claude_archive_sha256":EXPECTED_CLAUDE_SHA,"model_calls":0,
               "performance_measurements":0,"requests_total":540}
        atomic(out/"progress.json",state)

        extracted_old=out/"frozen-evidence"
        if not (extracted_old/"originals").exists():
            m.safe_extract_selected(evidence,extracted_old)

        extracted_claude=out/"claude-transfer"
        if not (extracted_claude/"manifest.json").exists():
            safe_extract_claude(claude,extracted_claude)
        else:
            need(sha(extracted_claude/"manifest.json")==EXPECTED_TRANSFER_MANIFEST_SHA,"existing extraction mismatch")

        ledger=jsonl(extracted_claude/"generation_ledger.jsonl")
        need(len(ledger)==540 and len({x["custom_id"] for x in ledger})==540,"ledger count/IDs")
        need(Counter(x["generation_status"] for x in ledger)=={"saved":515,"invalid_generation":25},"ledger status counts")

        box=m.Sandbox(out/"sandbox",args.cpu,args.node)
        m.sandbox_preflight(box,clang,out/"preflight")

        originals={}; baselines={}
        for task in sorted(m.CASES):
            for size in m.SIZES:
                oc=extracted_old/"originals"/task/size/"kernel.c"
                oi=extracted_old/"originals"/task/size/"kernel.ll"
                need(oc.is_file() and oi.is_file(),"missing frozen original")
                _,params=m.parse_kernel(oc.read_text(),task)
                originals[(task,size)]=(oc,oi,params)
                baselines[(task,size)]=m.native_case_baselines(box,clang,out/"baselines"/task/size,task,oc,params)
        state["baselines_completed"]=90; atomic(out/"progress.json",state)

        results=[]
        for i,row in enumerate(ledger,1):
            cid=row["custom_id"]; p=pid(cid); existing=result_path(out,cid)
            if existing.exists():
                r=load(existing)
            elif row["generation_status"]!="saved":
                r=generation_failure(row,out)
            else:
                src=extracted_claude/row["candidate_path"]
                need(src.is_file() and sha(src)==row["candidate_sha256"],"candidate SHA mismatch: "+cid)
                oc,oi,params=originals[(p["task"],p["size"])]
                vr={"condition":p["condition"],"id":cid,"task":p["task"],"size":p["size"],
                    "form":p["form"],"source":str(src),"source_sha256":row["candidate_sha256"],
                    "old_native_object":None}
                r=m.candidate_revalidate(box,clang,vr,oc,oi,params,baselines[(p["task"],p["size"])],
                                         out/"results"/p["condition"]/cid)
            results.append(r)
            state["candidates_terminal"]=i; state["passed"]=sum(bool(x.get("passed")) for x in results)
            atomic(out/"progress.json",state)
            if i%10==0 or not r.get("passed",False):
                print(f"{i}/540 {cid} status={r.get('status')} pass={r.get('passed')}",flush=True)

        summary={"completion":"CLAUDE_ZEN2_FULLSTATE_VALIDATION_COMPLETE",
                 "revision":"claude-sonnet5-zen2-fullstate-validation-v1",
                 "validator_revision":m.REV,"validator_sha256":EXPECTED_VALIDATOR_SHA,
                 "clang":ver,"requests_total":540,
                 "generation_failed":sum(r.get("status")=="generation_failed" for r in results),
                 "saved_candidates_revalidated":sum(r.get("status")!="generation_failed" for r in results),
                 "passed":sum(bool(r.get("passed")) for r in results),
                 "failed":sum(not bool(r.get("passed")) for r in results),
                 "by_condition":{},"by_form":{},"test_cases_per_kernel_source_size":2,
                 "profiles":["measured_native","generic","sanitized"],
                 "formal_equivalence_proven":False,"performance_measurements":0,"model_calls":0,
                 "scope":"Two custom runtime cases per original source-size with exact all-array final-state comparison; finite dynamic validation, not proof."}
        for c in ("P0","P1","P2"):
            rr=[r for r in results if r["condition"]==c]
            summary["by_condition"][c]={"total":len(rr),"passed":sum(bool(x.get("passed")) for x in rr),
                                        "generation_failed":sum(x.get("status")=="generation_failed" for x in rr)}
        for f in ("C","IR"):
            rr=[r for r in results if r["form"]==f]
            summary["by_form"][f]={"total":len(rr),"passed":sum(bool(x.get("passed")) for x in rr),
                                   "generation_failed":sum(x.get("status")=="generation_failed" for x in rr)}
        atomic(out/"summary.json",summary)
        state["completion"]=summary["completion"]; state["passed"]=summary["passed"]; atomic(out/"progress.json",state)
        print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
        print("CLAUDE_ZEN2_FULLSTATE_VALIDATION_COMPLETE",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--evidence",required=True); ap.add_argument("--claude",required=True)
    ap.add_argument("--validator",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--cpu",type=int,default=24); ap.add_argument("--node",type=int,default=1)
    run(ap.parse_args())
if __name__=="__main__": main()
