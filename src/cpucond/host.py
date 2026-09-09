"""Observe only allowlisted runtime host and tool information without inference."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from .models import CompilerTarget, HostObservation, SCHEMA_VERSION


def _capture(arguments: list[str]) -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            arguments, capture_output=True, text=True, timeout=10,
            check=False, encoding="utf-8", errors="replace",
            env={"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if result.returncode:
        return None, f"exit status {result.returncode}: {result.stderr.strip()}"
    return result.stdout.strip(), None


def observe_host() -> HostObservation:
    """Report what this process sees, including limitations of virtualized views."""
    methods: dict[str, str] = {}
    missing: dict[str, str] = {}
    os_name = platform.system() or None
    kernel = platform.release() or None
    architecture = platform.machine() or None
    methods.update(os_name="platform.system", kernel="platform.release", architecture="platform.machine")
    os_release = None
    try:
        distribution = platform.freedesktop_os_release()
        os_release = distribution.get("PRETTY_NAME") or distribution.get("NAME")
        methods["os_release"] = "platform.freedesktop_os_release (PRETTY_NAME/NAME only)"
    except OSError as exc:
        missing["os_release"] = f"OS release unavailable: {type(exc).__name__}"
    if os_release is None and "os_release" not in missing:
        missing["os_release"] = "OS release has no PRETTY_NAME or NAME"

    available_cpus = None
    if hasattr(os, "sched_getaffinity"):
        try:
            available_cpus = tuple(sorted(os.sched_getaffinity(0)))
            methods["available_cpus"] = "os.sched_getaffinity(0): CPUs allowed for this process"
        except OSError as exc:
            missing["available_cpus"] = f"affinity query failed: {type(exc).__name__}"
    else:
        missing["available_cpus"] = "os.sched_getaffinity is unavailable; CPU count is not an affinity set"
    logical_cpus = os.cpu_count()
    methods["logical_cpus"] = "os.cpu_count: logical CPUs visible to Python, possibly outside process affinity"
    if logical_cpus is None:
        missing["logical_cpus"] = "os.cpu_count returned None"

    version = platform.version()
    wsl = "microsoft" in ((kernel or "") + " " + version).lower()
    methods["wsl"] = "case-insensitive Microsoft marker in platform.release/platform.version"
    lscpu: dict[str, str] = {}
    lscpu_path = shutil.which("lscpu")
    lscpu_error = "lscpu executable was not found"
    if lscpu_path:
        # A private child environment selects stable field names; it is never logged.
        try:
            result = subprocess.run(
                [lscpu_path, "--json"], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=10, check=False,
                env={"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"},
            )
            if result.returncode:
                lscpu_error = f"lscpu exited with status {result.returncode}"
            else:
                data = json.loads(result.stdout)
                def collect(entries: list[dict]) -> None:
                    for entry in entries:
                        key, value = entry.get("field"), entry.get("data")
                        if isinstance(key, str) and isinstance(value, (str, int)):
                            lscpu[key.rstrip(":").strip()] = str(value).strip()
                        children = entry.get("children")
                        if isinstance(children, list):
                            collect(children)
                collect(data.get("lscpu", []))
                methods["lscpu"] = "lscpu --json with LC_ALL=C; allowlisted fields only"
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError) as exc:
            lscpu_error = f"lscpu observation failed: {type(exc).__name__}"

    cpu_model = lscpu.get("Model name") or None
    if cpu_model is None:
        missing["cpu_model"] = "lscpu did not expose Model name" if lscpu else lscpu_error
    else:
        methods["cpu_model"] = "lscpu: Model name; guest-visible value"
    flags = lscpu.get("Flags") or lscpu.get("Features")
    isa_flags = tuple(sorted(set(flags.split()))) if flags else None
    if isa_flags is None:
        missing["isa_flags"] = "lscpu did not expose Flags/Features" if lscpu else lscpu_error
    else:
        methods["isa_flags"] = "lscpu: Flags/Features; guest-visible advertised ISA"
    cache_keys = ("L1d cache", "L1i cache", "L2 cache", "L3 cache", "L4 cache")
    caches = {key: lscpu[key] for key in cache_keys if lscpu.get(key)} or None
    if caches is None:
        missing["caches"] = "No cache information exposed by lscpu; physical caches are not inferred"
    else:
        methods["caches"] = "lscpu cache summary; guest-visible aggregation, not verified physical cache topology"
    topology_keys = ("CPU(s)", "On-line CPU(s) list", "Thread(s) per core", "Core(s) per socket", "Socket(s)", "NUMA node(s)")
    topology = {key: lscpu[key] for key in topology_keys if lscpu.get(key)} or None
    if topology is None:
        missing["topology"] = "No CPU topology exposed by lscpu; physical core counts are not inferred"
    else:
        methods["topology"] = "lscpu topology; guest-visible CPU topology, not verified physical host cores"
    virtualization = {
        "hypervisor_vendor": lscpu.get("Hypervisor vendor") or None,
        "virtualization_type": lscpu.get("Virtualization type") or None,
        "cpu_virtualization_capability": lscpu.get("Virtualization") or None,
    }
    for key, value in virtualization.items():
        field = f"virtualization.{key}"
        if value is None:
            missing[field] = "Not exposed by lscpu; absence does not establish bare-metal execution"
        else:
            methods[field] = "lscpu; observed advertisement only, capability alone does not establish virtualization"
    return HostObservation(
        os_name=os_name, os_release=os_release, kernel=kernel, architecture=architecture,
        cpu_model=cpu_model, available_cpus=available_cpus, logical_cpus=logical_cpus,
        isa_flags=isa_flags, wsl=wsl, virtualization=virtualization, caches=caches,
        topology=topology, methods=methods, missing=missing,
        scope=(
            "WSL guest-visible and process-visible observations; physical Windows host "
            "topology, caches, frequencies, and scheduling are not inferred."
            if wsl else
            "Process-visible operating-system observations; physical host properties "
            "are not inferred and virtualization may limit visibility."
        ),
    )


def discover_compiler(compiler: str = "clang") -> CompilerTarget:
    """Resolve the executable and query version/target from that exact executable."""
    path = shutil.which(compiler)
    if path is None:
        raise FileNotFoundError(f"compiler executable not found: {compiler}")
    resolved = str(Path(path).resolve())
    version, error = _capture([resolved, "--version"])
    if error or not version:
        raise RuntimeError(f"could not query compiler version: {error or 'empty output'}")
    if "clang" not in version.lower():
        raise ValueError("Goal 001 requires Clang to emit LLVM IR; selected compiler is not Clang")
    triple, error = _capture([resolved, "-dumpmachine"])
    if error or not triple:
        raise RuntimeError(f"could not query compiler target: {error or 'empty output'}")
    return CompilerTarget(compiler=resolved, version=version, target_triple=triple)


def _tool_diagnostic(names: tuple[str, ...]) -> dict:
    path = next((found for name in names if (found := shutil.which(name))), None)
    if path is None:
        return {"available": False, "path": None, "version": None, "reason": f"not found: {', '.join(names)}"}
    resolved = str(Path(path).resolve())
    version, reason = _capture([resolved, "--version"])
    return {"available": reason is None and bool(version), "path": resolved, "version": version, "reason": reason}


def doctor() -> dict:
    """Read-only diagnostics; does not build, install packages, or contact a service."""
    compiler: dict
    try:
        compiler = {"available": True, **asdict(discover_compiler()), "reason": None}
    except (OSError, RuntimeError, ValueError) as exc:
        compiler = {"available": False, "reason": str(exc)}
    objdump = _tool_diagnostic(("llvm-objdump", "llvm-objdump-18"))
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": asdict(observe_host()),
        "compiler": compiler,
        "gcc": _tool_diagnostic(("gcc",)),
        "python": {
            "version": platform.python_version(), "executable": sys.executable,
            "virtual_environment": sys.prefix != sys.base_prefix,
        },
        "objdump": objdump,
        "ready": compiler["available"] and objdump["available"],
        "environment_role": "development_smoke",
        "publishable_benchmark": False,
    }
