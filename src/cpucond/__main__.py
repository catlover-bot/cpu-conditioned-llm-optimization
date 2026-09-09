import argparse
import json
from pathlib import Path

from .experiment import audit_artifacts, run_smoke
from .host import doctor


def main(argv=None):
    parser = argparse.ArgumentParser(description="CPU-conditioned optimization development smoke; no LLM API calls")
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
    verify = commands.add_parser("check-artifacts", help="verify a saved run's SHA-256 manifest")
    verify.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            report = doctor()
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if report.get("ready", True) else 1
        if args.command == "check-artifacts":
            errors = audit_artifacts(args.run)
            print(json.dumps({"passed": not errors, "errors": errors}, indent=2))
            return 1 if errors else 0
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
