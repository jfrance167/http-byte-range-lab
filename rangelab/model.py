"""Counterfactual GET geometry and hypothetical policy; never emits an HTTP response."""

import copy

from .contracts import validate

ASSUMPTIONS = [
    "Geometry is a counterfactual GET calculation over supplied representation octets.",
    "Coding spelling and length are metadata only; no resource read or decoding occurs.",
    "Baseline is a supplied completed normal/precondition outcome, not evaluated here.",
    "If-Range and server choice are assumptions, not observed validator or origin behavior.",
    "Status and Content-Range strings are explanatory hypotheses, never emitted HTTP.",
    "No authentication, resource mutation, cache merging, live transfer or full conformance claim.",
]


def _geometry(case):
    requested = case["range"]
    if requested is None:
        return "ABSENT", None, None
    length = case["representation"]["length"]
    if requested["kind"] == "suffix":
        suffix = requested["suffix"]
        if suffix == 0:
            return "UNSATISFIABLE", None, 0
        if length == 0:
            # Positive suffix is satisfiable by the standard; no nonempty interval exists.
            return "SATISFIABLE_EMPTY", None, 0
        first = max(0, length - suffix)
        last = length - 1
    else:
        first = requested["first"]
        if requested["kind"] == "closed" and requested["last"] < first:
            return "INVALID_RANGE", None, None
        if first >= length:
            return "UNSATISFIABLE", None, 0
        last = length - 1 if requested["kind"] == "open" else min(requested["last"], length - 1)
    return "SATISFIABLE", {"first": first, "last": last}, last - first + 1


def _if_range_state(case):
    if case["if_range"] == "absent":
        return "ABSENT"
    if case["range"] is None:
        return "IGNORED_NO_RANGE"
    if case["method"] != "GET":
        return "IGNORED_METHOD"
    if case["baseline_status"] != 200:
        return "NOT_REACHED_BASELINE"
    if case["server_policy"] == "ignore":
        return "IGNORED_SERVER_CHOICE"
    return {"match": "PASS", "mismatch": "FAIL", "unknown": "UNKNOWN"}[case["if_range"]]


def _handling(case, math, interval):
    baseline = case["baseline_status"]
    if case["range"] is None:
        return "NO_RANGE", baseline, None
    if case["method"] != "GET":
        return "IGNORE_METHOD", baseline, None
    if baseline != 200:
        return "IGNORE_BASELINE", baseline, None
    if case["server_policy"] == "ignore":
        return "IGNORE_SERVER_CHOICE", 200, None
    if case["if_range"] == "mismatch":
        return "IGNORE_IF_RANGE", 200, None
    if case["if_range"] == "unknown":
        return "UNSUPPORTED_IF_RANGE", None, None
    if math == "INVALID_RANGE":
        return "IGNORE_INVALID_LAB_POLICY", 200, None
    if math == "SATISFIABLE_EMPTY":
        return "UNSUPPORTED_EMPTY_SUFFIX_HANDLING", None, None
    length = case["representation"]["length"]
    if math == "UNSATISFIABLE":
        return "REJECT_UNSATISFIABLE_LAB_POLICY", 416, f"bytes */{length}"
    return "HONOR_SINGLE_RANGE", 206, f'bytes {interval["first"]}-{interval["last"]}/{length}'


def _result(case):
    if case["scope"]:
        math, interval, count = "UNKNOWN_CONTEXT", None, None
        handling, status, header = "UNSUPPORTED_CONTEXT", None, None
        trace, reasons = "UNKNOWN_CONTEXT", case["scope"]
    else:
        math, interval, count = _geometry(case)
        if case["baseline_status"] < 200:
            handling, status, header = "UNSUPPORTED_INFORMATIONAL_BASELINE", None, None
            trace = "UNKNOWN_BASELINE"
        else:
            handling, status, header = _handling(case, math, interval)
            trace = _if_range_state(case)
        reasons = [handling]
    declaration = copy.deepcopy({key: value for key, value in case.items() if key not in {"id", "scope"}})
    return {"id": case["id"], "status": "UNSUPPORTED" if handling.startswith("UNSUPPORTED") else "SUPPORTED",
            "reason_codes": list(reasons), "math_state": math, "interval": interval,
            "byte_count": count, "handling": handling, "hypothetical_status": status,
            "hypothetical_content_range": header, "if_range_state": trace, "declaration": declaration}


def evaluate(document):
    """Return fresh inert records after full validation; never evaluates actual origins."""
    cases = validate(document)
    return {"version": 1, "results": [_result(case) for case in cases], "assumptions": list(ASSUMPTIONS)}
