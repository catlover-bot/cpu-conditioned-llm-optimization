"""Predeclare blind, paired candidate-selection tasks without acquiring answers.

Only explicit source code, execution conditions and allowlisted CPU observations
reach prompts. The prior diagnostic run is audited as provenance, never used as
an answer table. This module executes neither candidates nor model calls.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import random
import re

from .diagnostic_config import DiagnosticConfig, QualityPolicy
from .diagnostic_prompts import _common_payload
from .experiment import audit_artifacts
from .host import observe_host
from .models import CompilerTarget, ExecutionContract
from .prompts import CPU_SECTION_HEADER
from .transformations import FACTORS, FIXTURES, make_candidates


SCHEMA_VERSION = "3.0"
CANDIDATE_IDS = tuple(f"unroll_{factor}" for factor in FACTORS)
DEFAULT_CONFIG = {
    "sizes": [128, 256],
    "input_seed": 17,
    "trials_per_condition": 5,
    "order_seed": 2026003,
    "target": {"destination": "local_same_host", "compiler_mode": "preserve_source_run", "measurement_cpu": None},
    "cpu_context": {"source": "source_run_observation"},
    "near_tie_fraction": 0.03,
    "size_rationale": "Two preregistered development sizes; this task was seen during development and is not held out.",
}
_HOST_FIELDS = ("architecture", "cpu_model", "isa_flags", "logical_cpus", "caches", "topology", "virtualization", "wsl")
_CACHE_FIELDS = ("L1d cache", "L1i cache", "L2 cache", "L3 cache", "L4 cache")
_TOPOLOGY_FIELDS = ("CPU(s)", "On-line CPU(s) list", "Thread(s) per core", "Core(s) per socket", "Socket(s)", "NUMA node(s)")
_VIRTUALIZATION_FIELDS = ("hypervisor_vendor", "virtualization_type", "cpu_virtualization_capability")


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text_hash(text: str) -> str:
    return _sha(text.encode("utf-8"))


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def host_fingerprint(host: dict) -> dict:
    """Stable process-visible target fields; never a verified physical identity.

    Affinity and kernel version are excluded: a measurement can legitimately
    restrict affinity and OS updates do not identify a different physical CPU.
    Matching fingerprints support an observation match, not physical identity.
    """
    if not isinstance(host, dict):
        raise ValueError("host observation must be an object")
    result = {key: deepcopy(host.get(key)) for key in _HOST_FIELDS}
    for key, fields in (("caches", _CACHE_FIELDS), ("topology", _TOPOLOGY_FIELDS), ("virtualization", _VIRTUALIZATION_FIELDS)):
        original = result[key]
        result[key] = {field: original.get(field) for field in fields if original.get(field) is not None} if isinstance(original, dict) else None
    if result["isa_flags"] is not None:
        result["isa_flags"] = sorted(set(result["isa_flags"]))
    return result


def _config(config: dict | None) -> dict:
    if config is not None and not isinstance(config, dict):
        raise ValueError("selection configuration must be a JSON object")
    supplied = config or {}
    if set(supplied) - set(DEFAULT_CONFIG):
        raise ValueError("unknown selection configuration keys")
    result = deepcopy(DEFAULT_CONFIG)
    for key, value in supplied.items():
        if key in ("target", "cpu_context"):
            if not isinstance(value, dict) or set(value) - set(DEFAULT_CONFIG[key]):
                raise ValueError(f"invalid {key} configuration")
            result[key].update(deepcopy(value))
        else:
            result[key] = deepcopy(value)
    sizes = result["sizes"]
    if not isinstance(sizes, list) or len(sizes) != 2 or any(type(n) is not int or not 1 <= n <= 1024 for n in sizes) or len(set(sizes)) != 2:
        raise ValueError("the pilot requires two distinct integer sizes in 1..1024")
    if type(result["input_seed"]) is not int or not 0 <= result["input_seed"] <= 0xFFFFFFFF:
        raise ValueError("input_seed must be a uint32 integer")
    if type(result["trials_per_condition"]) is not int or result["trials_per_condition"] != 5:
        raise ValueError("the balanced five-option pilot requires exactly five trials per condition")
    if type(result["order_seed"]) is not int:
        raise ValueError("order_seed must be an integer")
    target = result["target"]
    if target["destination"] != "local_same_host" or target["compiler_mode"] != "preserve_source_run":
        raise ValueError("only the local same-host destination with the preserved CompilerTarget is currently implemented")
    if target["measurement_cpu"] is not None and (type(target["measurement_cpu"]) is not int or target["measurement_cpu"] < 0):
        raise ValueError("measurement_cpu must be a nonnegative integer or null")
    if result["cpu_context"]["source"] not in ("source_run_observation", "current_host_observation"):
        raise ValueError("CPU text must come from a recorded or current observation; external CPU specifications are not implemented")
    fraction = result["near_tie_fraction"]
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or not 0 <= fraction < 1:
        raise ValueError("near_tie_fraction must be finite and in [0, 1)")
    if not isinstance(result["size_rationale"], str) or not result["size_rationale"].strip():
        raise ValueError("size_rationale must be a nonempty explanation fixed before responses")
    return result


def _compiler(compiler: dict) -> CompilerTarget:
    data = deepcopy(compiler)
    for key in ("target_flags", "optimization_flags", "floating_point_flags", "link_flags"):
        data[key] = tuple(data[key])
    target = CompilerTarget(**data)
    if target.target_flags or target.link_flags:
        raise ValueError("this pilot preserves only the audited compiler-default generic target; native/explicit targets require a separate implementation")
    if target.optimization_flags != ("-O3",) or target.floating_point_flags != ("-fno-fast-math", "-ffp-contract=off"):
        raise ValueError("the pilot requires the unchanged strict diagnostic compiler flags")
    return target


def _compiler_disclosure(compiler: dict) -> dict:
    target = _compiler(compiler)
    if not isinstance(target.target_triple, str) or not re.fullmatch(r"[A-Za-z0-9_.+-]+", target.target_triple):
        raise ValueError("an observed compiler target triple is required for the common ISA contract")
    match = re.search(r"\bclang version\s+([0-9]+(?:\.[0-9]+)+)", target.version, re.IGNORECASE)
    if not match:
        raise ValueError("an observed numeric Clang version is required for common disclosure")
    return {
        "compiler": "Clang", "version": match[1], "target_triple": target.target_triple,
        "target_mode": "compiler_default_generic", "language": "C11",
        "optimization_flags": list(target.optimization_flags),
        "floating_point_flags": list(target.floating_point_flags),
        "target_flags": [], "link_time_optimization": False,
        "available_instructions": (
            "Only the compiler-default ISA for this target triple; no native CPU tuning or additional ISA feature flags. "
            "Additional advertised CPU capabilities do not authorize instructions outside this common compilation contract."
        ),
        "compilation": "Common driver and kernel are compiled as separate translation units with the same kernel ABI.",
    }


def _cpu_context(observation: dict, source: str) -> dict:
    observed = host_fingerprint(observation)
    lines = [
        "These are recorded guest-visible or process-visible CPU observations, not independently verified physical hardware specifications.",
        f"Observation source: {source}; allowlisted fields of HostObservation.",
        "Physical CPU identity, physical cache topology and physical frequencies: unknown (not independently verified).",
    ]
    for key in _HOST_FIELDS:
        value = observed[key]
        rendered = "unknown (not exposed by the observation)" if value is None else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        lines.append(f"{key}: {rendered}")
    return {
        "text": "\n".join(lines) + "\n", "source": source,
        "scope": "Guest/process-visible observations only; not verified physical hardware and not inferred from PC names.",
        "observations": observed, "physical_hardware_verified": False,
        "physical_hardware_specification": "unknown",
    }


def _policies(config: dict) -> dict:
    return {
        "first_attempt_policy": "first_attempt_only",
        "first_attempt_explanation": "The first imported attempt, including an invalid response, is primary; later attempts are retained and never replace it.",
        "invalid_answers": "Record invalid JSON, multiple/unknown selections and request-ID mismatches without correction; retain the denominator.",
        "missing_answers": "Record unanswered requests; retain the denominator and leave timing/ratio values null.",
        "measurement_phase": "confirmation",
        "quality_diagnostics": "New-run cross-phase rank warnings are reused only for judgment; numerical scoring uses confirmation only.",
        "measurement_source": "new_run_after_response_freeze",
        "shared_measurement": "One independently measured confirmation table is shared by all answers; answer count is not an independent measurement count.",
        "near_tie_fraction": config["near_tie_fraction"],
        "near_tie_definition": "(selected candidate median time / minimum median time among the five verified candidates) - 1 <= near_tie_fraction",
        "near_tie_action": "Treat as a practical near tie, not a binary correctness decision or proof of statistical equivalence.",
        "quality_warning_action": "withhold_decisive_judgment",
        "quality_warning_explanation": "Retain observations and warnings; withhold decisive judgment when timing quality or blinding is insufficient.",
        "offline_policies": [*(f"always_unroll_{factor}" for factor in FACTORS), "uniform_random_exact_expectation"],
        "offline_policy_scope": "Fixed and uniform-random policies are scored offline on the same five-candidate measurement table; this is not LLM search.",
        "metrics": ["response_invalid_missing_counts", "selection_frequencies", "selected_time_and_reference_ratio",
                    "paired_none_spec_selection_changes", "all_fixed_and_uniform_random_policies",
                    "loss_from_observed_best_within_five_candidates", "near_ties_quality_and_judgment_withholding"],
        "statistical_significance_test": False,
        "baseline": "reference", "controls": ["identity", "deliberately_wrong"],
        "performance_gate": "No speedup, code difference, winning condition or particular option is required for software success.",
    }


def _blinding() -> dict:
    return {
        "required": {"independent_session": True, "no_tools": True, "no_prior_results": True},
        "declaration_status": "self_reported_not_independently_verified",
        "prior_task_performance_seen_by_developers": True, "task_is_unseen_or_held_out": False,
        "implementing_agent_must_not_supply_evaluation_answers": True,
        "manual_path_limitations": "Record unverified isolation/tool-use/history limitations; do not infer or fabricate independent-session compliance.",
    }


def _request_payload(base: dict, compiler: dict, request_id: str, size: int, seed: int, ordered: list[str], sources: dict) -> tuple[dict, dict]:
    payload = deepcopy(base)
    payload["task"] = (
        "Choose one of the five supplied C kernels for the common target execution conditions. "
        "Use only this prompt in an independent session; do not use execution, search or other tools, prior results, or other trial answers. "
        "This is a small diagnostic selection pilot, not free-form code optimization or an unseen benchmark."
    )
    payload["request_id"] = request_id
    payload["input"] = {
        "size": size, "seed": seed, "dtype": "IEEE-754 binary64",
        "layout": "Disjoint contiguous row-major n-by-n a, b, and c; c starts at positive zero.",
        "initialization": (
            "Initialize uint32 state from seed; for each flat index generate a then b by state=(1664525*state+1013904223) mod 2^32, "
            "value=(state >> 15)/65536.0-1.0. Each invocation starts from the same initialized arrays."
        ),
    }
    payload["compiler_contract"] = _compiler_disclosure(compiler)
    mapping = {f"option_{position:02d}": candidate_id for position, candidate_id in enumerate(ordered, 1)}
    payload["options"] = [{"option_id": option, "source": sources[internal]["source"]} for option, internal in mapping.items()]
    payload["output_format"] = {
        "format": "One JSON object, without Markdown fences or other text.",
        "required_fields": {"request_id": request_id, "selected_option_id": "Exactly one supplied option ID."},
        "optional_fields": {"rationale_short": "Optional brief explanation, at most 500 Unicode characters; do not provide extended internal reasoning."},
        "additional_fields": False,
    }
    return payload, mapping


def _requests(protocol: dict):
    candidates = []
    canonical = {item.candidate_id: item for item in make_candidates()}
    for name in ("reference", *CANDIDATE_IDS):
        source = protocol["reference"] if name == "reference" else protocol["candidates"][name]
        candidates.append(replace(canonical[name], source=source["source"]))
    base, _ = _common_payload(candidates, ExecutionContract())
    rng = random.Random(protocol["config"]["order_seed"])
    for size in protocol["config"]["sizes"]:
        initial_order = list(CANDIDATE_IDS)
        rng.shuffle(initial_order)
        for index in range(5):
            request_id = f"n{size}-t{index + 1:02d}"
            order = initial_order[index:] + initial_order[:index]
            payload, mapping = _request_payload(base, protocol["compiler"], request_id, size, protocol["config"]["input_seed"], order, protocol["candidates"])
            common = canonical_json(payload)
            for condition in ("none", "spec"):
                key = request_id + "-" + condition
                prompt = common + (CPU_SECTION_HEADER + protocol["cpu_context"]["text"] + "\n" if condition == "spec" else "")
                request = {
                    "request_key": key, "request_id": request_id, "size": size, "seed": protocol["config"]["input_seed"],
                    "trial": index + 1, "condition": condition, "option_mapping": mapping,
                    "prompt_path": f"requests/{key}/prompt.txt", "prompt_sha256": _text_hash(prompt),
                    "common_payload_path": f"requests/{key}/common_payload.json", "common_payload_sha256": _text_hash(common),
                    "raw_response_path": f"incoming/{key}/response.txt", "metadata_path": f"incoming/{key}/metadata.json",
                    "metadata_template_path": f"requests/{key}/metadata-template.json",
                    "import_command_argv": [
                        "python", "-m", "cpucond", "pilot", "import", "<pilot_directory>",
                        "--request-key", key,
                        "--response", f"<pilot_directory>/incoming/{key}/response.txt",
                        "--metadata", f"<pilot_directory>/incoming/{key}/metadata.json",
                    ],
                    "import_instructions": (
                        "Replace <pilot_directory> in each argument with this pilot directory. "
                        "Save the independent session's original answer at raw_response_path, and copy the metadata template "
                        "to metadata_path before filling only actually available identification and acquisition information. "
                        "The argv list is an import command description; no response text is executed."
                    ),
                }
                yield request, common, prompt


def _metadata(request: dict, cohort: str) -> dict:
    return {
        "cohort": cohort,
        "acquisition_method": "manual_transcription" if cohort == "real" else "synthetic_fixture",
        "acquisition_source": None, "model_identifier": None, "obtained_at": None,
        "prompt_hash": request["prompt_sha256"], "generation_settings": None, "usage": None,
        "missing_reasons": {
            "acquisition_source": "Fill the actual acquisition source if known; it has not been provided.",
            "model_identifier": "No independently acquired model identification has been supplied." if cohort == "real" else "Synthetic software fixture; no actual model was used.",
            "obtained_at": "No response has yet been acquired.",
            "generation_settings": "Generation settings have not been supplied and must not be inferred.",
            "usage": "Usage has not been supplied and must not be inferred.",
        },
        "blinding": {
            "independent_session": None, "no_tools": None, "no_prior_results": None,
            "limitations": ["Manual transfer alone does not independently verify session isolation, tool use, prior-result exposure, or model identity."],
        },
    }


def export_protocol(directory: Path, *, source_run: Path, config: dict | None = None, cohort: str = "real") -> dict:
    """Export a frozen task set into a new or existing empty directory.

    The 20 unique request keys distinguish conditions, while each none/spec
    pair shares its response request_id so the CPU description is the sole
    prompt difference. Metadata templates are editable copies only after moving
    them to incoming/. Original prompts, templates and source snapshots are static.
    """
    directory, source_run = Path(directory).resolve(), Path(source_run).resolve()
    config = _config(config)
    if cohort not in ("real", "synthetic"):
        raise ValueError("cohort must be real or synthetic")
    if directory.is_relative_to(source_run) or directory == source_run:
        raise ValueError("pilot output must not modify or be inside the source run")
    if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
        raise FileExistsError("protocol export requires an empty destination directory")
    errors = audit_artifacts(source_run)
    if errors:
        raise ValueError("source diagnostic artifacts failed validation: " + "; ".join(errors[:5]))
    source = json.loads((source_run / "experiment.json").read_text(encoding="utf-8"))
    if source.get("experiment_type") != "controlled_diagnostics" or source.get("status") != "completed":
        raise ValueError("the source must be a completed controlled diagnostic run")
    compiler = deepcopy(source["compiler"])
    _compiler_disclosure(compiler)
    current_observation = asdict(observe_host())
    cpu_source = config["cpu_context"]["source"]
    cpu_observation = source["host"] if cpu_source == "source_run_observation" else current_observation
    measurement_config = deepcopy(source["settings"])
    measurement_config["measure_cases"] = [[size, config["input_seed"]] for size in config["sizes"]]
    measurement_config["size_rationale"] = config["size_rationale"]
    protocol = {
        "schema_version": SCHEMA_VERSION, "experiment_type": "blind_candidate_selection_pilot", "export_cohort": cohort,
        "environment_role": "development_smoke", "publishable_benchmark": False,
        "kernel": "gemm_smoke", "config": config,
        "source_run": {"path": str(source_run), "run_id": source["run_id"],
                       "experiment_sha256": _sha((source_run / "experiment.json").read_bytes()),
                       "manifest_sha256": source["manifest_sha256"], "git": deepcopy(source["git"])},
        "compiler": compiler, "target_mode": "compiler_default_generic", "target": config["target"],
        "measurement_config": measurement_config,
        "source_target_host": host_fingerprint(source["host"]), "current_target_host": host_fingerprint(current_observation),
        "cpu_context": _cpu_context(cpu_observation, cpu_source), "execution_contract": asdict(ExecutionContract()),
        "request_identity_scope": "request_id identifies one size/trial pair and is shared by none/spec; request_key uniquely identifies size/trial/condition and is required for import.",
        "presentation_order": "Seeded initial permutation per size, followed by five cyclic rotations; each candidate occupies each position once per condition.",
        "blinding": _blinding(),
        "policies": _policies(config), "candidates": {}, "reference": {}, "controls": {}, "shared_sources": {}, "requests": [],
    }
    source_contents = {}
    for candidate in make_candidates():
        text = (source_run / "candidates" / candidate.candidate_id / "kernel.c").read_text(encoding="utf-8")
        if text != candidate.source:
            raise ValueError("source run candidate differs from the declared deterministic family")
        item = {"source": text, "source_sha256": _text_hash(text), "source_path": f"sources/{candidate.candidate_id}.c"}
        source_contents[item["source_path"]] = text
        if candidate.candidate_id == "reference":
            protocol["reference"] = item
        elif candidate.candidate_id in CANDIDATE_IDS:
            protocol["candidates"][candidate.candidate_id] = item
        else:
            protocol["controls"][candidate.candidate_id] = item
    for filename in ("kernel.h", "harness.c"):
        content = (source_run / "candidates/reference" / filename).read_text(encoding="utf-8")
        path = f"sources/{filename}"
        source_contents[path] = content
        protocol["shared_sources"][filename] = {"path": path, "sha256": _text_hash(content)}
    request_contents = {}
    for request, common, prompt in _requests(protocol):
        protocol["requests"].append(request)
        request_contents[request["common_payload_path"]] = common
        request_contents[request["prompt_path"]] = prompt
        request_contents[request["metadata_template_path"]] = canonical_json(_metadata(request, cohort))
    # Validate the measurement configuration as the existing runner will use it.
    _measurement_config(protocol["measurement_config"])
    directory.mkdir(parents=True, exist_ok=True)
    for path, content in {**source_contents, **request_contents}.items():
        _write(directory / path, content)
    _write(directory / "protocol.json", canonical_json(protocol))
    manifest = {path.relative_to(directory).as_posix(): _sha(path.read_bytes()) for path in sorted(directory.rglob("*")) if path.is_file()}
    _write(directory / "static-manifest.json", canonical_json(manifest))
    return protocol


def _measurement_config(value: dict) -> DiagnosticConfig:
    data = deepcopy(value)
    for key in ("verification_sizes", "verification_seeds"):
        data[key] = tuple(data[key])
    data["measure_cases"] = tuple(tuple(case) for case in data["measure_cases"])
    data["quality"] = QualityPolicy(**data["quality"])
    return DiagnosticConfig(**data)


def validate_protocol(directory: Path) -> list[str]:
    """Read-only validation from saved static data; the source run need not exist.

    Mutable incoming/ and lifecycle files are outside this module's manifest.
    The lifecycle layer binds protocol/static-manifest hashes and code provenance.
    """
    directory = Path(directory)
    errors = []

    def check(condition, reason):
        if not condition:
            errors.append(reason)

    try:
        protocol = json.loads((directory / "protocol.json").read_text(encoding="utf-8"))
        check(protocol["schema_version"] == SCHEMA_VERSION and protocol["experiment_type"] == "blind_candidate_selection_pilot", "unsupported selection protocol")
        check(protocol["environment_role"] == "development_smoke" and protocol["publishable_benchmark"] is False, "invalid pilot environment classification")
        check(protocol["export_cohort"] in ("real", "synthetic"), "invalid protocol cohort")
        config = _config(protocol["config"])
        check(config == protocol["config"] and protocol["target"] == config["target"], "target/configuration differs from its validated form")
        _compiler_disclosure(protocol["compiler"])
        check(protocol["target_mode"] == "compiler_default_generic", "compiler target mode was changed")
        measurement = _measurement_config(protocol["measurement_config"])
        check(measurement.measure_cases == tuple((size, config["input_seed"]) for size in config["sizes"]), "request inputs differ from measurement inputs")
        check(protocol["execution_contract"] == asdict(ExecutionContract()), "common execution/correctness contract was changed")
        check(protocol["policies"] == _policies(config), "response/scoring policy differs from its fixed implementation")
        check(protocol["blinding"] == _blinding(), "blinding and prior-exposure policy was changed")
        cpu_source = config["cpu_context"]["source"]
        observed = protocol["source_target_host"] if cpu_source == "source_run_observation" else protocol["current_target_host"]
        check(protocol["cpu_context"] == _cpu_context(observed, cpu_source), "CPU text is not the allowlisted recorded observation")
        check(set(protocol["candidates"]) == set(CANDIDATE_IDS) and set(protocol["controls"]) == {"identity", "deliberately_wrong"}, "candidate or control set differs from the five-option family")
        expected_paths = {"protocol.json"}
        for candidate in make_candidates():
            item = protocol["reference"] if candidate.candidate_id == "reference" else (protocol["candidates"] if candidate.candidate_id in CANDIDATE_IDS else protocol["controls"])[candidate.candidate_id]
            expected = {"source": candidate.source, "source_sha256": _text_hash(candidate.source), "source_path": f"sources/{candidate.candidate_id}.c"}
            check(item == expected, f"frozen candidate source/hash changed: {candidate.candidate_id}")
            expected_paths.add(expected["source_path"])
            check((directory / expected["source_path"]).read_bytes() == candidate.source.encode("utf-8"), f"source snapshot differs: {candidate.candidate_id}")
        for filename in ("kernel.h", "harness.c"):
            item = protocol["shared_sources"][filename]
            expected_path = f"sources/{filename}"
            check(item["path"] == expected_path, f"unexpected shared-source path: {filename}")
            check(_sha((directory / expected_path).read_bytes()) == item["sha256"], f"shared-source snapshot hash differs: {filename}")
            check((directory / expected_path).read_bytes() == (FIXTURES / filename).read_bytes(), f"common driver/ABI source differs from the diagnostic contract: {filename}")
            expected_paths.add(expected_path)
        reconstructed = list(_requests(protocol))
        check(protocol["requests"] == [item[0] for item in reconstructed] and len(protocol["requests"]) == 20, "request plan/mapping/hashes differs from the fixed balanced paired plan")
        for request, common, prompt in reconstructed:
            for key, content in (("common_payload_path", common), ("prompt_path", prompt), ("metadata_template_path", canonical_json(_metadata(request, protocol["export_cohort"])))):
                expected_paths.add(request[key])
                check((directory / request[key]).read_bytes() == content.encode("utf-8"), f"request artifact differs from blinded protocol: {request['request_key']}/{key}")
        manifest = json.loads((directory / "static-manifest.json").read_text(encoding="utf-8"))
        # The lifecycle layer seals additional runner/provenance files and checks
        # their complete allowed set; this module owns requests/ and sources/.
        check(expected_paths.issubset(manifest), "static manifest is missing required protocol files")
        for path in expected_paths:
            check(manifest.get(path) == _sha((directory / path).read_bytes()), f"static artifact hash differs: {path}")
        for folder in ("requests", "sources"):
            actual = {path.relative_to(directory).as_posix() for path in (directory / folder).rglob("*") if path.is_file()}
            check(actual == {path for path in expected_paths if path.startswith(folder + "/")}, f"unexpected or missing static files under {folder}")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append(f"invalid or incomplete selection protocol: {exc}")
    return errors
