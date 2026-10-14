"""All-element IEEE-754 binary64 validation, not a proof of equivalence."""

import json
import re


class OutputError(ValueError):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def parse_output(text: str, expected_count: int) -> list[int]:
    lines = text.splitlines()
    if not lines:
        raise OutputError("empty_output")
    if not re.fullmatch(r"CPUCOND_F64 [0-9]{1,10}", lines[0]):
        raise OutputError("invalid_header")
    count = int(lines[0].split()[1])
    if count != expected_count or len(lines) - 1 != expected_count:
        raise OutputError("element_count_mismatch")
    values = []
    for line in lines[1:]:
        if not re.fullmatch(r"[0-9a-f]{16}", line):
            raise OutputError("invalid_float64_bits")
        bits = int(line, 16)
        if bits & 0x7FF0000000000000 == 0x7FF0000000000000:
            raise OutputError("non_finite_output")
        values.append(bits)
    return values


def validate_result(result, expected_count, expected=None):
    if result.category != "ok":
        return {"passed": False, "category": result.category, "reason": "process_failed"}, None
    try:
        actual = parse_output(result.stdout, expected_count)
    except OutputError as exc:
        return {"passed": False, "category": "output_format_error", "reason": exc.reason}, None
    if expected is not None:
        if len(expected) != expected_count:
            raise ValueError("reference element count does not match contract")
        mismatches = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
        if mismatches:
            first = mismatches[0]
            return {"passed": False, "category": "value_mismatch", "mismatch_count": len(mismatches),
                    "first_index": first, "expected_bits": f"{expected[first]:016x}",
                    "actual_bits": f"{actual[first]:016x}"}, actual
    return {"passed": True, "category": "ok", "elements_compared": expected_count}, actual


def parse_measurement(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise OutputError("invalid_measurement_json") from exc
    if not isinstance(data, dict) or set(data) != {"elapsed_ns", "checksum_bits"}:
        raise OutputError("invalid_measurement_fields")
    elapsed = data["elapsed_ns"]
    if type(elapsed) is not int or elapsed <= 0:
        raise OutputError("non_positive_or_invalid_elapsed_ns")
    if not isinstance(data["checksum_bits"], str) or not re.fullmatch(r"[0-9a-f]{16}", data["checksum_bits"]):
        raise OutputError("invalid_checksum_bits")
    return data
