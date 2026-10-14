"""Offline analysis of the published GPU004 primary/GPU005 reuse cohort.

Only local CSV/JSON and small CUDA source bytes are read. No runtime executors,
provider clients, GPU bindings, compilers or network modules are imported.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "research-artifacts"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def rows(path):
    with Path(path).open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def candidate_integrity(data_root=DEFAULT_ROOT):
    root=Path(data_root)/"gpu004"
    index=read_json(root/"candidate-index.json")
    if len({r["id"] for r in index})!=len(index):
        raise ValueError("Duplicate candidate ID")
    for row in index:
        path=Path(row["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe candidate path")
        source=root/path
        if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest()!=row["source_sha256"]:
            raise ValueError("Candidate hash differs")
    return index

def summarize(data_root=DEFAULT_ROOT):
    root=Path(data_root)
    source=read_json(root/"gpu004/outcomes.json")
    primary=read_json(root/"gpu004/summary.json")
    source_by_id={r["id"]:r for r in source}
    if len(source_by_id)!=len(source):
        raise ValueError("Duplicate primary outcome ID")
    saved={r["id"]:r for r in source if r["generation_status"]=="saved"}
    index=candidate_integrity(root)
    if {r["id"] for r in index}!=set(saved):
        raise ValueError("Candidate publication coverage differs")
    for row in index:
        if row["source_sha256"]!=saved[row["id"]]["source_sha256"]:
            raise ValueError("Primary/candidate identity differs")
    result={"gpu004":{"candidate_slots":len(source),"generation_status_counts":dict(Counter(r["generation_status"] for r in source)),
                       "providers":dict(Counter(r["provider"] for r in source)),
                       "trials":sorted({r["trial"] for r in source}),
                       "csv_rows":len(rows(root/"gpu004/outcomes.csv")),
                       "historical_prior_270_plan_complete":primary["prior_270_plan_complete"],
                       "formal_equivalence_proven":primary["formal_equivalence_proven"]},"gpu005":{}}
    for profile in ("a40","l4"):
        folder=root/"gpu005"/profile
        outcomes=read_json(folder/"outcomes.json")
        summary=read_json(folder/"summary.json")
        controls=read_json(folder/"controls.json")
        table=rows(folder/"outcomes.csv")
        by_id={r["id"]:r for r in outcomes}
        if set(by_id)!=set(source_by_id):
            raise ValueError("Reevaluation coverage differs")
        for ident,original in saved.items():
            if by_id[ident]["source_sha256"]!=original["source_sha256"]:
                raise ValueError("Reevaluation source differs")
        for row in table:
            if row["speedup"] and not math.isfinite(float(row["speedup"])):
                raise ValueError("Nonfinite reported speedup")
        result["gpu005"][profile]={"source_slots":summary["source_slots"],
                                   "target_candidate_slots":summary["target_candidate_slots"],
                                   "new_generation_calls":summary["new_generation_calls"],
                                   "coverage_rows":len(rows(folder/"coverage_90.csv")),
                                   "result_rows":len(table),"unique_measured_ids":len({r["id"] for r in table}),
                                   "comparisons":dict(Counter(r["comparison"] for r in table)),
                                   "control_cells":len(controls),
                                   "valid_control_cells":sum(r["measurement_valid"] is True for r in controls),
                                   "declared_valid_control_cells":summary["valid_control_cells"],
                                   "formal_equivalence_proven":summary["formal_equivalence_proven"],
                                   "selection_used_confirmation":summary["selection_used_confirmation"]}
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root",type=Path,default=DEFAULT_ROOT)
    args=parser.parse_args(argv)
    print(json.dumps(summarize(args.data_root),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
