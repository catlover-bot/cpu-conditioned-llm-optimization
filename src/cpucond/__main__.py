import argparse
import json
from pathlib import Path

from .experiment import audit_artifacts, run_smoke
from .host import doctor


def main(argv=None):
    parser = argparse.ArgumentParser(description="CPU-conditioned optimization development smoke and local selection pilot")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="observe the local development environment")
    smoke = commands.add_parser("smoke", help="verify and measure handwritten C fixtures")
    smoke.add_argument("--output", type=Path, default=Path("runs/goal001"), help="parent of a new unique run directory")
    smoke.add_argument("--spec-file", type=Path, help="explicit UTF-8 CPU specification for the spec prompt")
    smoke.add_argument("--compiler", default="clang")
    smoke.add_argument("--input-kind", choices=("c", "llvm_ir", "asm"), default="c")
    smoke.add_argument("--repeats", type=int, default=6)
    smoke.add_argument("--warmups", type=int, default=2)
    smoke.add_argument("--cpu", type=int)
    diagnose = commands.add_parser("diagnose", help="compare deterministic C unroll factors with separate confirmation")
    diagnose.add_argument("--output", type=Path, default=Path("runs/goal002"))
    diagnose.add_argument("--config", type=Path, help="predeclared JSON diagnostic settings")
    diagnose.add_argument("--spec-file", type=Path, help="explicit CPU description, used only in offline prompts")
    diagnose.add_argument("--compiler", default="clang")
    diagnose.add_argument("--cpu", type=int)
    verify = commands.add_parser("check-artifacts", help="verify a saved run's SHA-256 manifest")
    verify.add_argument("run", type=Path)
    pilot = commands.add_parser("pilot", help="blind candidate-selection pilot with manual or local acquisition")
    pilot_commands = pilot.add_subparsers(dest="pilot_command", required=True)
    prepare = pilot_commands.add_parser("prepare", help="freeze a protocol and export 20 blind requests")
    prepare.add_argument("--source-run", type=Path, required=True)
    prepare.add_argument("--output", type=Path, default=Path("runs/goal003"))
    prepare.add_argument("--config", type=Path)
    prepare.add_argument("--cohort", choices=("real", "synthetic"), default="real")
    local_prepare = pilot_commands.add_parser("prepare-local", help="seal a new real local cohort from a manual task")
    local_prepare.add_argument("--source-pilot", type=Path, required=True)
    local_prepare.add_argument("--local-config", type=Path, required=True)
    local_prepare.add_argument("--output", type=Path, default=Path("runs/goal003.1"))
    local_prepare.add_argument("--evidence", type=Path, action="append", default=[])
    for name in ("local-preflight", "local-run", "local-unload", "local-check"):
        local_action = pilot_commands.add_parser(name, help="Ollama local acquisition lifecycle")
        local_action.add_argument("pilot", type=Path)
        if name in ("local-preflight", "local-run"):
            local_action.add_argument("--timeout", type=float, default=1800)
        if name == "local-run":
            local_action.add_argument("--limit", type=int)
    collect = pilot_commands.add_parser("import", help="store one raw response as a new immutable attempt")
    collect.add_argument("pilot", type=Path)
    collect.add_argument("--request-key", required=True)
    collect.add_argument("--response", type=Path, required=True)
    collect.add_argument("--metadata", type=Path, required=True)
    for name, help_text in (("freeze", "close response collection before independent measurement"),
                            ("score", "run a fresh shared diagnostic and score frozen answers"),
                            ("status", "count real/synthetic, invalid, and missing responses"),
                            ("check", "audit protocol, attempts, freeze, measurement, and policy reports"),
                            ("synthetic", "fill only a synthetic cohort with plumbing fixtures")):
        pilot_commands.add_parser(name, help=help_text).add_argument("pilot", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "pilot":
            from .selection import (prepare_pilot, read_json, import_answer, freeze_answers,
                                    score_pilot, pilot_status, check_pilot, synthetic_answers)
            if args.pilot_command == "prepare":
                config = read_json(args.config) if args.config else None
                directory, status = prepare_pilot(args.output, args.source_run, config=config, cohort=args.cohort)
                result = {"pilot_directory": str(directory), **status}
            elif args.pilot_command == "prepare-local":
                from .local_cohort import prepare_local_pilot
                directory, status = prepare_local_pilot(args.output, args.source_pilot, read_json(args.local_config),
                                                        evidence_files=args.evidence)
                result = {"pilot_directory": str(directory), **status}
            elif args.pilot_command.startswith("local-"):
                from .local_llm import preflight_local, run_local, unload_local, audit_local
                if args.pilot_command == "local-preflight":
                    result = preflight_local(args.pilot, timeout=args.timeout)
                elif args.pilot_command == "local-run":
                    result = run_local(args.pilot, limit=args.limit, timeout=args.timeout)
                elif args.pilot_command == "local-unload":
                    result = unload_local(args.pilot)
                else:
                    result = audit_local(args.pilot)
            elif args.pilot_command == "import":
                imported = import_answer(args.pilot, args.request_key, args.response, args.metadata)
                result = {"attempt": {key: imported["attempt"][key] for key in
                                      ("request_key", "attempt_id", "status", "invalid_reason", "primary_attempt")},
                          "pilot": imported["pilot"]}
            else:
                action = {"freeze": freeze_answers, "score": score_pilot, "status": pilot_status,
                          "check": check_pilot, "synthetic": synthetic_answers}[args.pilot_command]
                result = action(args.pilot)
                if args.pilot_command == "freeze":
                    result = {"freeze_path": str(args.pilot / "freeze.json"), **{key: result[key] for key in
                              ("cohort", "protocol_sha256", "frozen_utc", "counts")}}
                elif args.pilot_command == "score":
                    result = {"pilot": result["pilot"], "score_path": str(args.pilot / "score.json"),
                              "measurement_directory": result["score"]["measurement_directory"],
                              "reports": result["score"]["reports"], "independent_measurement_runs": 1}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 1 if result.get("passed") is False else 0
        if args.command == "doctor":
            report = doctor()
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if report.get("ready", True) else 1
        if args.command == "check-artifacts":
            errors = audit_artifacts(args.run)
            print(json.dumps({"passed": not errors, "errors": errors}, indent=2))
            return 1 if errors else 0
        if args.command == "diagnose":
            from .diagnostic_config import DiagnosticConfig, load_config
            from .diagnostics import run_diagnostics
            config = load_config(args.config) if args.config else DiagnosticConfig()
            specification = args.spec_file.read_text(encoding="utf-8") if args.spec_file else None
            run_dir, record = run_diagnostics(args.output, config=config, specification=specification,
                                             compiler=args.compiler, cpu=args.cpu)
            print(json.dumps({"run_directory": str(run_dir), "status": record["status"],
                              "environment_role": record["environment_role"], "publishable_benchmark": False,
                              "report": str(run_dir / "report.md"), "artifact_errors": record.get("artifact_errors", [])}, indent=2))
            return 0 if record["status"] == "completed" else 1
        specification = args.spec_file.read_text(encoding="utf-8") if args.spec_file else None
        run_dir, record = run_smoke(args.output, specification=specification, compiler=args.compiler,
                                   input_kind=args.input_kind, repeats=args.repeats, warmups=args.warmups, cpu=args.cpu)
        print(json.dumps({"run_directory": str(run_dir), "status": record["status"],
                          "environment_role": record["environment_role"],
                          "publishable_benchmark": record["publishable_benchmark"],
                          "verification": {name: x["verification"]["category"] for name, x in record["candidates"].items()}}, indent=2))
        return 0 if record["status"] == "completed" else 1
    except (ValueError, OSError, RuntimeError, NotImplementedError) as exc:
        parser.exit(1, f"cpucond: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
