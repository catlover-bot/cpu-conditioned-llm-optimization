"""Predeclared controls for the single-family development diagnostic."""

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class QualityPolicy:
    min_median_ns: int = 100_000
    max_relative_iqr: float = 0.20
    rank_tolerance: int = 1
    near_tie_fraction: float = 0.03

    def __post_init__(self):
        if type(self.min_median_ns) is not int or self.min_median_ns <= 0:
            raise ValueError("min_median_ns must be a positive integer")
        if type(self.rank_tolerance) is not int or self.rank_tolerance < 0:
            raise ValueError("rank_tolerance must be a nonnegative integer")
        for value in (self.max_relative_iqr, self.near_tie_fraction):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("quality fractions must be finite and nonnegative")


@dataclass(frozen=True)
class DiagnosticConfig:
    verification_sizes: tuple[int, ...] = (1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17)
    verification_seeds: tuple[int, ...] = (1, 17, 42)
    measure_cases: tuple[tuple[int, int], ...] = ((128, 17), (256, 17))
    repeats: int = 8
    warmups: int = 2
    exploration_order_seed: int = 2026002
    confirmation_order_seed: int = 2026003
    timeout_seconds: float = 30.0
    quality: QualityPolicy = field(default_factory=QualityPolicy)
    size_rationale: str = "Two preregistered small development sizes, 128 and 256; not representative research workloads."

    def __post_init__(self):
        if any(type(group) is not tuple for group in (self.verification_sizes, self.verification_seeds, self.measure_cases)):
            raise ValueError("input sets must be immutable tuples")
        if any(type(case) is not tuple or len(case) != 2 for case in self.measure_cases):
            raise ValueError("measure_cases must contain (size, seed) tuples")
        if not self.verification_sizes or not self.verification_seeds or not self.measure_cases:
            raise ValueError("verification and measurement inputs cannot be empty")
        all_sizes = (*self.verification_sizes, *(n for n, _ in self.measure_cases))
        all_seeds = (*self.verification_seeds, *(s for _, s in self.measure_cases))
        if any(type(n) is not int or not 1 <= n <= 1024 for n in all_sizes):
            raise ValueError("matrix sizes must be integers in 1..1024")
        if any(type(s) is not int or not 0 <= s <= 0xFFFFFFFF for s in all_seeds):
            raise ValueError("input seeds must be uint32 integers")
        if len(set(self.measure_cases)) != len(self.measure_cases):
            raise ValueError("measurement cases must be unique")
        if type(self.repeats) is not int or self.repeats < 2 or type(self.warmups) is not int or self.warmups < 0:
            raise ValueError("need repeats >= 2 and warmups >= 0")
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)) or not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        if any(type(s) is not int for s in (self.exploration_order_seed, self.confirmation_order_seed)):
            raise ValueError("order seeds must be integers")
        if self.exploration_order_seed == self.confirmation_order_seed:
            raise ValueError("exploration and confirmation must use distinct order seeds")
        if not isinstance(self.quality, QualityPolicy) or not isinstance(self.size_rationale, str) or not self.size_rationale.strip():
            raise ValueError("quality policy and an explicit size rationale are required")
        if not {1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17}.issubset(self.verification_sizes):
            raise ValueError("verification must include all unroll boundaries and their neighbors")
        if len(set(self.verification_seeds)) < 2:
            raise ValueError("verification requires multiple distinct seeds")

    def cases(self):
        return list(dict.fromkeys([(n, s) for n in self.verification_sizes for s in self.verification_seeds] + list(self.measure_cases)))

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))


def load_config(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("configuration must be a JSON object")
        for key in ("verification_sizes", "verification_seeds"):
            if key in data:
                data[key] = tuple(data[key])
        if "measure_cases" in data:
            data["measure_cases"] = tuple(tuple(case) for case in data["measure_cases"])
        if "quality" in data:
            data["quality"] = QualityPolicy(**data["quality"])
        return DiagnosticConfig(**data)
    except (TypeError, KeyError, AttributeError) as exc:
        raise ValueError(f"invalid diagnostic configuration: {exc}") from exc
