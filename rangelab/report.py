"""Bounded inert reports and exclusive fresh-file output."""

import json
import os

from .contracts import Invalid, OUTPUT_BYTES


def _entities(value):
    return "".join(f"&#{ord(char)};" for char in value)


def encode(report, format_name="json"):
    """Encode only evaluated reports; user IDs never become Markdown syntax."""
    if format_name == "json":
        source = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    elif format_name == "markdown":
        lines = ["# Offline byte-range geometry and assumed handling", "", "Counterfactual geometry and supplied policy; no resource or response action performed.", ""]
        for result in report["results"]:
            lines.extend(["## " + _entities(result["id"]), "", "| Field | Value |", "|---|---|"])
            for key, value in result.items():
                if key == "id":
                    continue
                value = json.dumps(value, ensure_ascii=True) if type(value) in (list, dict) else str(value)
                lines.append("| " + key + " | " + _entities(value) + " |")
            lines.append("")
        lines.extend(["", "Assumptions:", ""] + ["- " + _entities(item) for item in report["assumptions"]])
        source = "\n".join(lines) + "\n"
    else:
        raise Invalid("REPORT_FORMAT")
    payload = source.encode("utf-8", "strict")
    if len(payload) > OUTPUT_BYTES:
        raise Invalid("OUTPUT_LIMIT")
    return payload


def write_fresh(path, payload):
    """Create exclusively. Failed writes remove only this newly created file.

    This is not protection against a hostile process racing filesystem changes.
    The CLI-selected path is trusted; case content never chooses it.
    """
    stream = open(path, "xb")
    try:
        with stream:
            if stream.write(payload) != len(payload):
                raise OSError("SHORT_WRITE")
            stream.flush()
    except OSError:
        try:
            os.unlink(path)
        except OSError as exc:
            raise Invalid("OUTPUT_WRITE_AND_CLEANUP_FAILED") from exc
        raise

