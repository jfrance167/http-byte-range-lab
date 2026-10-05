"""Strict bounded contract validation, adapted from Jake's MIT HTTP-cache/CORS labs."""

import json
import re

INPUT_BYTES = 65_536
OUTPUT_BYTES = 262_144
MAX_INTEGER = 1_000_000_000
TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", re.ASCII)


class Invalid(ValueError):
    """Fixed error code: document cannot be evaluated under this contract."""


def text(value, limit=256, nonempty=False):
    """Validate scalar text without coercion, truncation or replacement."""
    if type(value) is not str or len(value) > limit or (nonempty and not value):
        raise Invalid("TEXT_TYPE_OR_LIMIT")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise Invalid("TEXT_CONTROL")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise Invalid("INVALID_UNICODE") from exc
    return value


def keys(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise Invalid("SCHEMA")


def number(value, lower=0, upper=MAX_INTEGER):
    if type(value) is not int or not lower <= value <= upper:
        raise Invalid("INTEGER_BOUND")
    return value


def _walk(value, depth, budget, active):
    # Reject custom containers before accessing their methods or iterating them.
    budget[0] += 1
    if budget[0] > 5_000:
        raise Invalid("NODE_LIMIT")
    kind = type(value)
    if kind in (dict, list):
        if id(value) in active:
            raise Invalid("CONTAINER_CYCLE")
        depth += 1
        if depth > 8 or len(value) > 100:
            raise Invalid("CONTAINER_LIMIT")
        active.add(id(value))
        try:
            if kind is dict:
                for key, item in value.items():
                    text(key, 64, True)
                    budget[0] += 1
                    if budget[0] > 5_000:
                        raise Invalid("NODE_LIMIT")
                    _walk(item, depth, budget, active)
            else:
                for item in value:
                    _walk(item, depth, budget, active)
        finally:
            active.remove(id(value))
    elif kind is str:
        text(value, 256)
    elif kind is int:
        number(value)
    elif kind is not bool and value is not None:
        raise Invalid("BUILTIN_DATA_REQUIRED")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _integer(token):
    if len(token.lstrip("-")) > 10:
        raise Invalid("NUMERIC_TOKEN_LIMIT")
    return int(token)


def _noninteger(_):
    raise Invalid("INTEGER_ONLY")


def parse(raw):
    """Decode exact bytes with byte/depth/token bounds; evaluate() validates schema."""
    if type(raw) is not bytes or len(raw) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    try:
        source = raw.decode("utf-8", "strict")
        quoted = escaped = False
        depth = 0
        for char in source:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 8:
                    raise Invalid("JSON_DEPTH")
            elif char in "]}":
                depth -= 1
        return json.loads(source, object_pairs_hook=_pairs, parse_int=_integer,
                          parse_float=_noninteger, parse_constant=_noninteger)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("INVALID_JSON") from exc


FEATURE = re.compile(r"[a-z][a-z0-9-]*", re.ASCII)


def _token(value, limit, code):
    text(value, limit, True)
    if not TOKEN.fullmatch(value):
        raise Invalid(code)
    return value


def _choice(value, choices, code):
    if type(value) is not str or value not in choices:
        raise Invalid(code)
    return value


def _range(value, scope):
    if value is None:
        return None
    keys(value, {"unit", "kind", "first", "last", "suffix"})
    unit = _token(value["unit"], 32, "UNIT_TOKEN")
    kind = _choice(value["kind"], {"closed", "open", "suffix"}, "RANGE_KIND")
    used = {"closed": {"first", "last"}, "open": {"first"}, "suffix": {"suffix"}}[kind]
    for name in ("first", "last", "suffix"):
        if name in used:
            number(value[name])
        elif value[name] is not None:
            raise Invalid("RANGE_SHAPE")
    if unit.lower() != "bytes":
        scope.add("UNSUPPORTED_UNIT")
    return dict(value)


def _case(value):
    keys(value, {"id", "method", "baseline_status", "representation", "range",
                 "server_policy", "if_range", "unsupported_features"})
    text(value["id"], 64, True)
    _token(value["method"], 16, "METHOD_TOKEN")
    number(value["baseline_status"], 100, 599)
    scope = set()
    representation = value["representation"]
    keys(representation, {"length", "content_coding", "length_basis"})
    length = representation["length"]
    if length is None:
        scope.add("UNSUPPORTED_LENGTH")
    else:
        number(length)
    coding = _token(representation["content_coding"], 32, "CODING_TOKEN")
    if coding.lower() not in {"identity", "gzip", "br"}:
        scope.add("UNSUPPORTED_CODING")
    basis = _choice(representation["length_basis"],
                    {"selected_representation_bytes", "decoded_bytes", "unknown"}, "LENGTH_BASIS")
    if basis != "selected_representation_bytes":
        scope.add("UNSUPPORTED_LENGTH_BASIS")
    requested = _range(value["range"], scope)
    _choice(value["server_policy"], {"honor", "ignore"}, "SERVER_POLICY")
    _choice(value["if_range"], {"absent", "match", "mismatch", "unknown"}, "IF_RANGE_STATE")
    features = value["unsupported_features"]
    if type(features) is not list or len(features) > 8:
        raise Invalid("FEATURE_LIMIT")
    for feature in features:
        text(feature, 32, True)
        if not FEATURE.fullmatch(feature):
            raise Invalid("FEATURE_IDENTIFIER")
    if len(set(features)) != len(features):
        raise Invalid("DUPLICATE_FEATURE")
    if features:
        scope.add("UNSUPPORTED_FEATURE")
    return {"id": value["id"], "method": value["method"], "baseline_status": value["baseline_status"],
            "representation": dict(representation), "range": requested,
            "server_policy": value["server_policy"], "if_range": value["if_range"],
            "unsupported_features": list(features), "scope": sorted(scope)}


def validate(document):
    """Validate the entire concrete tree and all cases before any semantic result."""
    _walk(document, 0, [0], set())
    if len(json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    keys(document, {"version", "cases"})
    if type(document["version"]) is not int or document["version"] != 1:
        raise Invalid("VERSION")
    cases = document["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= 40:
        raise Invalid("CASE_LIMIT")
    result, seen = [], set()
    for value in cases:
        case = _case(value)
        if case["id"] in seen:
            raise Invalid("DUPLICATE_ID")
        seen.add(case["id"])
        result.append(case)
    return result




