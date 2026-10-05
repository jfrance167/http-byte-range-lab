"""Independent frozen labels, tiny index oracle and interface delivery checks."""

import ast
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
# Fixed interpreter and own module; no shell or input-selected commands.
import subprocess  # nosec B404
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from rangelab import Invalid, evaluate, parse
from rangelab.contracts import INPUT_BYTES, OUTPUT_BYTES
from rangelab.report import encode, write_fresh

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8-sig"))
EXPECTED = json.loads((ROOT / "fixtures/expected.json").read_text(encoding="utf-8"))


def one():
    return {"version": 1, "cases": [copy.deepcopy(DOCUMENT["cases"][0])]}


def requested(kind, first=None, last=None, suffix=None):
    return {"unit": "bytes", "kind": kind, "first": first, "last": last, "suffix": suffix}


def result(doc):
    return evaluate(doc)["results"][0]


@contextmanager
def scratch():
    temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="test-scratch-")
    if not Path(temporary.name).resolve().is_relative_to(ROOT):
        raise RuntimeError("temporary path outside project")
    try:
        yield Path(temporary.name)
    finally:
        temporary.cleanup()


class LabTests(unittest.TestCase):
    def test_frozen_labels(self):
        rows = evaluate(DOCUMENT)["results"]
        self.assertEqual(len(rows), 40)
        for actual, expected in zip(rows, EXPECTED):
            with self.subTest(case=expected["id"]):
                self.assertEqual({key: actual[key] for key in expected}, expected)
        self.assertEqual(sum(row["status"] == "UNSUPPORTED" for row in rows), 12)

    def test_frozen_bytes(self):
        receipt = json.loads((ROOT / "research/fixture-freeze.json").read_text(encoding="utf-8-sig"))
        for entry in receipt:
            name = entry["Path"].replace("\\", "/").split("/")[-1]
            path = ROOT / name if name == "CONTRACT.md" else ROOT / "fixtures" / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest().upper(), entry["Hash"])

    def test_independent_tiny_index_oracle(self):
        # Invented integer indices only: no body/file slicing, and not the production formula.
        checked = 0
        for length in range(1, 9):
            for kind in ("closed", "open", "suffix"):
                for a in range(0, 11):
                    ends = range(a, 11) if kind == "closed" else [None]
                    for b in ends:
                        doc = one()
                        case = doc["cases"][0]
                        case["representation"]["length"] = length
                        case["range"] = (requested(kind, a, b) if kind != "suffix"
                                         else requested(kind, suffix=a))
                        selected = []
                        for index in range(length):
                            includes = ((kind == "closed" and a <= index <= b)
                                        or (kind == "open" and index >= a)
                                        or (kind == "suffix" and length - index <= a))
                            if includes:
                                selected.append(index)
                        actual = result(doc)
                        wanted = {"first": selected[0], "last": selected[-1]} if selected else None
                        self.assertEqual(actual["interval"], wanted)
                        self.assertEqual(actual["byte_count"], len(selected))
                        self.assertEqual(actual["math_state"], "SATISFIABLE" if selected else "UNSATISFIABLE")
                        checked += 1
        self.assertEqual(checked, 704)

    def test_empty_and_zero_suffix_distinction(self):
        for suffix, math, handling in [(0, "UNSATISFIABLE", "REJECT_UNSATISFIABLE_LAB_POLICY"),
                                       (1, "SATISFIABLE_EMPTY", "UNSUPPORTED_EMPTY_SUFFIX_HANDLING"),
                                       (1_000_000_000, "SATISFIABLE_EMPTY", "UNSUPPORTED_EMPTY_SUFFIX_HANDLING")]:
            doc = one()
            case = doc["cases"][0]
            case["representation"]["length"] = 0
            case["range"] = requested("suffix", suffix=suffix)
            actual = result(doc)
            self.assertEqual((actual["math_state"], actual["handling"]), (math, handling))
            self.assertIsNone(actual["interval"])
            self.assertEqual(actual["byte_count"], 0)
            if suffix:
                self.assertIsNone(actual["hypothetical_status"])
                self.assertIsNone(actual["hypothetical_content_range"])

    def test_reversed_is_invalid_not_unsatisfiable(self):
        doc = one()
        doc["cases"][0]["range"] = requested("closed", 10, 9)
        actual = result(doc)
        self.assertEqual(actual["math_state"], "INVALID_RANGE")
        self.assertIsNone(actual["byte_count"])
        self.assertEqual(actual["hypothetical_status"], 200)

    def test_units_coding_case_and_provenance(self):
        for unit in ("bytes", "BYTES", "bYtEs"):
            for coding in ("identity", "IDENTITY", "GZIP", "Br"):
                doc = one()
                case = doc["cases"][0]
                case["range"]["unit"] = unit
                case["representation"]["content_coding"] = coding
                actual = result(doc)
                self.assertEqual(actual["status"], "SUPPORTED")
                self.assertEqual(actual["declaration"]["range"]["unit"], unit)
                self.assertEqual(actual["declaration"]["representation"]["content_coding"], coding)

    def test_informational_geometry_but_unknown_handling(self):
        for baseline in (100, 103, 199):
            doc = one()
            doc["cases"][0]["baseline_status"] = baseline
            actual = result(doc)
            self.assertEqual(actual["interval"], {"first": 2, "last": 4})
            self.assertIsNone(actual["hypothetical_status"])
            self.assertEqual(actual["if_range_state"], "UNKNOWN_BASELINE")

    def test_absent_global_scope_and_sorted_reasons(self):
        doc = one()
        case = doc["cases"][0]
        case["range"] = None
        case["baseline_status"] = 304
        case["representation"].update(length=None, content_coding="custom", length_basis="decoded_bytes")
        case["unsupported_features"] = ["multipart"]
        actual = result(doc)
        self.assertEqual(actual["reason_codes"], ["UNSUPPORTED_CODING", "UNSUPPORTED_FEATURE",
                                                 "UNSUPPORTED_LENGTH", "UNSUPPORTED_LENGTH_BASIS"])
        self.assertEqual(actual["math_state"], "UNKNOWN_CONTEXT")
        self.assertIsNone(actual["byte_count"])
        self.assertIsNone(actual["hypothetical_status"])

    def test_if_range_match_trace_and_method_case(self):
        for method, handling, trace in [("GET", "HONOR_SINGLE_RANGE", "PASS"),
                                        ("get", "IGNORE_METHOD", "IGNORED_METHOD"),
                                        ("POST", "IGNORE_METHOD", "IGNORED_METHOD")]:
            doc = one()
            doc["cases"][0].update(method=method, if_range="match")
            actual = result(doc)
            self.assertEqual((actual["handling"], actual["if_range_state"]), (handling, trace))

    def test_all_completed_non200_baselines_ignored(self):
        for baseline in (201, 204, 206, 301, 304, 403, 412, 416, 500, 599):
            doc = one()
            doc["cases"][0].update(baseline_status=baseline, if_range="mismatch")
            actual = result(doc)
            self.assertEqual(actual["handling"], "IGNORE_BASELINE")
            self.assertEqual(actual["hypothetical_status"], baseline)
            self.assertEqual(actual["if_range_state"], "NOT_REACHED_BASELINE")

    def test_late_invalid_before_any_semantic_result(self):
        for early in ({"server_policy": "ignore"}, {"unsupported_features": ["multipart"]},
                      {"baseline_status": 304}, {"range": None}):
            doc = one()
            doc["cases"][0].update(early)
            late = copy.deepcopy(doc["cases"][0])
            late["id"] = "late"
            late["representation"]["length"] = True
            doc["cases"].append(late)
            with patch("rangelab.model._result") as semantic:
                with self.assertRaises(Invalid):
                    evaluate(doc)
                semantic.assert_not_called()

    def test_input_types_shapes_and_conflicting_values(self):
        changes = [("version", True), ("cases", []), ("cases", DOCUMENT["cases"] + [DOCUMENT["cases"][0]])]
        for key, value in changes:
            doc = one()
            doc[key] = value
            with self.assertRaises(Invalid):
                evaluate(doc)
        for field, value in [("method", "GET "), ("server_policy", []), ("if_range", {}),
                             ("baseline_status", 99), ("baseline_status", True), ("unknown", "x")]:
            doc = one()
            doc["cases"][0][field] = value
            with self.assertRaises(Invalid):
                evaluate(doc)
        for request in (requested("closed", True, 3), requested("open", 2, 3),
                        requested("suffix", first=0, suffix=1), requested([], 0, 1),
                        requested("open", -1), requested("open", 1_000_000_001)):
            doc = one()
            doc["cases"][0]["range"] = request
            with self.assertRaises(Invalid):
                evaluate(doc)
        for basis in (None, [], "arbitrary"):
            doc = one()
            doc["cases"][0]["representation"]["length_basis"] = basis
            with self.assertRaises(Invalid):
                evaluate(doc)

    def test_feature_validation_even_when_ignored(self):
        for features in (["multipart"] * 2, ["Bad"], ["a"] * 9, [True], {}):
            doc = one()
            doc["cases"][0].update(range=None, server_policy="ignore", unsupported_features=features)
            with self.assertRaises(Invalid):
                evaluate(doc)

    def test_api_cycles_custom_types_and_aliases(self):
        doc = one()
        doc["cases"].append(doc)
        with self.assertRaisesRegex(Invalid, "CONTAINER_CYCLE"):
            evaluate(doc)
        class Hostile(dict):
            def items(self):
                raise RuntimeError("must never run")
        with self.assertRaises(Invalid):
            evaluate(Hostile())
        with self.assertRaises(Invalid):
            evaluate(iter([one()]))
        doc = one()
        other = copy.deepcopy(doc["cases"][0])
        other["id"] = "other"
        other["representation"] = doc["cases"][0]["representation"]
        doc["cases"].append(other)
        self.assertEqual(len(evaluate(doc)["results"]), 2)

    def test_no_input_or_result_alias_mutation(self):
        doc = one()
        original = copy.deepcopy(doc)
        report = evaluate(doc)
        report["results"][0]["declaration"]["representation"]["length"] = 7
        report["results"][0]["interval"]["first"] = 8
        report["assumptions"].clear()
        self.assertEqual(doc, original)
        self.assertEqual(result(doc)["byte_count"], 3)

    def test_exact_result_schema_and_complete_declarations(self):
        report = evaluate(DOCUMENT)
        self.assertEqual(set(report), {"version", "results", "assumptions"})
        fields = {"id", "status", "reason_codes", "math_state", "interval", "byte_count",
                  "handling", "hypothetical_status", "hypothetical_content_range",
                  "if_range_state", "declaration"}
        for case, row in zip(DOCUMENT["cases"], report["results"]):
            self.assertEqual(set(row), fields)
            self.assertEqual(row["declaration"], {key: value for key, value in case.items() if key != "id"})

    def test_parser_lexical_depth_and_json_authority(self):
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}', b'{"x":1.0}', b'{"x":1e2}',
                    b'{"x":12345678901}', b'\xff', b'{', b'[' * 9 + b'0' + b']' * 9):
            with self.assertRaises(Invalid):
                parse(raw)
        # Escaped quote/backslash and braces in string cannot alter the depth gate.
        doc = one()
        doc["cases"][0]["id"] = '[[[[[[[[[\\"}quote'
        self.assertEqual(result(parse(json.dumps(doc).encode()))["id"], doc["cases"][0]["id"])
        with self.assertRaises(Invalid):
            parse(bytearray(b"{}"))

    def test_unicode_controls_and_duplicate_ids(self):
        for identity in ("a\x00", "a\x7f", "\ud800", "x" * 65):
            doc = one()
            doc["cases"][0]["id"] = identity
            with self.assertRaises(Invalid):
                evaluate(doc)
        doc = one()
        doc["cases"].append(copy.deepcopy(doc["cases"][0]))
        with self.assertRaisesRegex(Invalid, "DUPLICATE_ID"):
            evaluate(doc)
        with self.assertRaises(Invalid):
            evaluate(parse(b'{"version":1,"cases":[],"\\u0076ersion":1}'))

    def test_aggregate_input_depth_node_container_limits(self):
        with self.assertRaises(Invalid):
            parse(b" " * (INPUT_BYTES + 1))
        deep = []
        for _ in range(9):
            deep = [deep]
        with self.assertRaises(Invalid):
            evaluate(deep)
        with self.assertRaises(Invalid):
            evaluate([0] * 101)
        with self.assertRaisesRegex(Invalid, "NODE_LIMIT"):
            evaluate([[0] * 100 for _ in range(60)])
        with self.assertRaisesRegex(Invalid, "INPUT_LIMIT"):
            evaluate([["x" * 256] * 100 for _ in range(4)])

    def test_complete_report_fields_and_inert_markdown(self):
        doc = one()
        identity = '[click](https://example.test)|<img src=x>\\`_'
        doc["cases"][0]["id"] = identity
        report = evaluate(doc)
        payload = encode(report, "markdown").decode()
        self.assertNotIn(identity, payload)
        self.assertNotIn("<img", payload)
        self.assertIn("&#91;", payload)
        for key in report["results"][0]:
            if key != "id":
                self.assertIn("| " + key + " |", payload)
        self.assertEqual(json.loads(encode(report))["results"][0]["id"], identity)
        with self.assertRaisesRegex(Invalid, "OUTPUT_LIMIT"):
            # Honest evaluated-reporter seam; not claimed reachable through valid input.
            with patch("rangelab.report.OUTPUT_BYTES", 10):
                encode(report)
        with self.assertRaises(Invalid):
            encode(report, "html")
        self.assertLess(len(encode(evaluate(DOCUMENT), "markdown")), OUTPUT_BYTES)

    def test_fresh_output_never_overwrites(self):
        with scratch() as root:
            target = root / "new.json"
            write_fresh(target, b"original")
            with self.assertRaises(FileExistsError):
                write_fresh(target, b"replacement")
            self.assertEqual(target.read_bytes(), b"original")

    def test_short_flush_close_write_and_cleanup_errors(self):
        for failure in ("short", "flush", "close"):
            stream = MagicMock()
            stream.__enter__.return_value = stream
            stream.write.return_value = 1 if failure == "short" else 3
            if failure == "flush":
                stream.flush.side_effect = OSError("synthetic private error")
            if failure == "close":
                stream.__exit__.side_effect = OSError("synthetic private error")
            with patch("rangelab.report.open", return_value=stream), patch("rangelab.report.os.unlink") as unlink:
                with self.assertRaises(OSError):
                    write_fresh("owned-new-file", b"abc")
                unlink.assert_called_once_with("owned-new-file")
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.write.side_effect = OSError()
        with patch("rangelab.report.open", return_value=stream), patch("rangelab.report.os.unlink", side_effect=OSError()):
            with self.assertRaisesRegex(Invalid, "OUTPUT_WRITE_AND_CLEANUP_FAILED"):
                write_fresh("owned-new-file", b"abc")

    def cli(self, *arguments, optimized=False):
        return subprocess.run([sys.executable] + (["-O"] if optimized else []) + ["-m", "rangelab", *arguments],
                              cwd=ROOT, capture_output=True, timeout=15, check=False)  # nosec B603

    def test_actual_cli_supported_unsupported_invalid_and_alias(self):
        for optimized in (False, True):
            with scratch() as root:
                source = root / "input.json"
                source.write_text(json.dumps(one()), encoding="utf-8")
                child = self.cli(str(source), optimized=optimized)
                self.assertEqual(child.returncode, 0)
                self.assertEqual(json.loads(child.stdout)["results"][0]["byte_count"], 3)
                child = self.cli("fixtures/cases.json", optimized=optimized)
                self.assertEqual(child.returncode, 2)
                self.assertEqual(len(json.loads(child.stdout)["results"]), 40)
                child = self.cli(str(source), "--output", str(source), optimized=optimized)
                self.assertEqual(child.returncode, 1)
                self.assertIn(b"INPUT_OUTPUT_ALIAS", child.stderr)
                source.write_bytes(b"invalid")
                child = self.cli(str(source), optimized=optimized)
                self.assertEqual(child.returncode, 1)
                self.assertEqual(child.stdout, b"")
                self.assertIn(b"INVALID_JSON", child.stderr)

    def test_actual_cli_fresh_markdown_existing_and_missing_paths(self):
        with scratch() as root:
            target = root / "demo.md"
            child = self.cli("fixtures/cases.json", "--format", "markdown", "--output", str(target))
            self.assertEqual(child.returncode, 2)
            initial = target.read_bytes()
            self.assertIn(b"&#", initial)
            child = self.cli("fixtures/cases.json", "--output", str(target))
            self.assertEqual(child.returncode, 1)
            self.assertEqual(target.read_bytes(), initial)
            child = self.cli(str(root / "absent.json"))
            self.assertEqual(child.returncode, 1)
            self.assertEqual(child.stderr.replace(b"\r\n", b"\n"), b"rangelab: IO_ERROR\n")
            self.assertEqual(self.cli().returncode, 2)

    def test_actual_closed_stdout_at_four_sizes(self):
        with scratch() as root:
            for count in (6, 12, 24, 40):
                source = root / (str(count) + ".json")
                source.write_text(json.dumps({"version": 1, "cases": DOCUMENT["cases"][:count]}), encoding="utf-8")
                command = [sys.executable] + (["-O"] if sys.flags.optimize else []) + ["-m", "rangelab", str(source)]
                child = subprocess.Popen(command, cwd=ROOT,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec B603
                child.stdout.close()
                child.stdout = None  # communicate must not start a reader on the closed pipe.
                _, errors = child.communicate(timeout=15)
                self.assertNotEqual(child.returncode, 120)
                if child.returncode in (0, 2):
                    self.assertEqual(errors, b"")  # Complete small write can precede reader closure.
                else:
                    self.assertEqual(child.returncode, 1)
                    self.assertEqual(errors.replace(b"\r\n", b"\n"), b"rangelab: IO_ERROR\n")

    def test_cli_short_and_flush_stdout_fixed_errors(self):
        from rangelab.__main__ import main
        for failure in ("short", "flush"):
            stdout, stderr = MagicMock(), MagicMock()
            stdout.buffer.write.return_value = 0
            if failure == "flush":
                stdout.buffer.write.side_effect = lambda payload: len(payload)
                stdout.buffer.flush.side_effect = OSError("private-message")
            with patch("rangelab.__main__.sys.stdout", stdout), patch("rangelab.__main__.sys.stderr", stderr), \
                    patch("rangelab.__main__._silence_failed_stdout", return_value=True):
                self.assertEqual(main(["fixtures/cases.json"]), 1)
                stderr.write.assert_called_once_with("rangelab: IO_ERROR\n")

    def test_stdout_silence_failure_is_disclosed(self):
        from rangelab.__main__ import main
        stdout, stderr = MagicMock(), MagicMock()
        stdout.buffer.write.side_effect = OSError()
        with patch("rangelab.__main__.sys.stdout", stdout), patch("rangelab.__main__.sys.stderr", stderr), \
                patch("rangelab.__main__._silence_failed_stdout", return_value=False):
            self.assertEqual(main(["fixtures/cases.json"]), 1)
            stderr.write.assert_called_once_with("rangelab: STDOUT_WRITE_AND_SILENCE_FAILED\n")

    def barrier_cli(self, arguments, optimized, closed=()):
        # Owned wrapper gates main until pipes are closed; JSON argv avoids OS NUL argv restrictions.
        wrapper = ("import json,sys; from rangelab.__main__ import main; "
                   "sys.stdin.buffer.read(1); raise SystemExit(main(json.loads(sys.argv[1])))")
        command = [sys.executable] + (["-O"] if optimized else []) + ["-c", wrapper, json.dumps(arguments)]
        child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec B603
        try:
            for name in closed:
                getattr(child, name).close()
                setattr(child, name, None)
            child.stdin.write(b"x")
            child.stdin.close()
            child.stdin = None
            output, errors = child.communicate(timeout=15)
            return child.returncode, output, errors
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=15)
            for name in ("stdin", "stdout", "stderr"):
                handle = getattr(child, name)
                if handle is not None:
                    handle.close()

    def test_actual_empty_output_nul_and_argument_privacy(self):
        for optimized in (False, True):
            scenarios = [(["fixtures/cases.json", "--output", ""], 1, b"INVALID_OUTPUT_PATH"),
                         (["\x00private-path"], 1, b"INVALID_INPUT_PATH"),
                         (["fixtures/cases.json", "--output", "private\x00path"], 1, b"INVALID_OUTPUT_PATH"),
                         (["--unrecognized-private-value"], 2, b"ARGUMENT_ERROR")]
            for arguments, expected, message in scenarios:
                code, output, errors = self.barrier_cli(arguments, optimized)
                self.assertEqual(code, expected)
                self.assertEqual(output, b"")
                self.assertEqual(errors.replace(b"\r\n", b"\n"), b"rangelab: " + message + b"\n")
                self.assertNotIn(b"private", errors)

    def test_actual_both_failed_sinks_help_arguments_and_missing_input(self):
        for optimized in (False, True):
            for closed in (("stderr",), ("stdout", "stderr")):
                for arguments, expected in [(["missing-synthetic-private-file.json"], 1), ([], 2),
                                            (["--bad-private-value"], 2)]:
                    code, output, errors = self.barrier_cli(arguments, optimized, closed)
                    self.assertEqual(code, expected)
                    self.assertIn(output, (None, b""))
                    self.assertIsNone(errors)
            code, output, errors = self.barrier_cli(["--help"], optimized)
            self.assertEqual(code, 0)
            self.assertIn(b"usage: rangelab", output)
            self.assertLess(len(output), 4096)
            self.assertEqual(errors, b"")
            code, output, errors = self.barrier_cli(["--help"], optimized, ("stdout", "stderr"))
            self.assertEqual(code, 1)
            self.assertIsNone(output)
            self.assertIsNone(errors)
            code, output, errors = self.barrier_cli(["fixtures/cases.json"], optimized, ("stdout", "stderr"))
            self.assertEqual(code, 1)
            self.assertIsNone(output)
            self.assertIsNone(errors)

    def test_checked_diagnostic_short_flush_and_sink_silencing(self):
        from rangelab.__main__ import main
        class Sink:
            def __init__(self, mode):
                self.mode = mode
                self.messages = []
            def write(self, message):
                self.messages.append(message)
                if self.mode == "write":
                    raise OSError("private-native-error")
                return len(message) - 1 if self.mode == "short" else len(message)
            def flush(self):
                if self.mode == "flush":
                    raise OSError("private-native-error")
        for mode in ("write", "short", "flush"):
            for arguments, wanted in [(["missing-private-path.json"], 1), ([], 2)]:
                sink = Sink(mode)
                with patch("rangelab.__main__.sys.stderr", sink), \
                        patch("rangelab.__main__.os.open", side_effect=OSError()):
                    self.assertEqual(main(arguments), wanted)
                    self.assertIsNone(sys.stderr)
                self.assertEqual(sink.messages, ["rangelab: " + ("IO_ERROR" if wanted == 1 else "ARGUMENT_ERROR") + "\n"])
        stdout, stderr = MagicMock(), Sink("flush")
        stdout.buffer.write.side_effect = OSError("private-native-error")
        with patch("rangelab.__main__.sys.stdout", stdout), patch("rangelab.__main__.sys.stderr", stderr), \
                patch("rangelab.__main__.os.open", side_effect=OSError()):
            self.assertEqual(main(["fixtures/cases.json"]), 1)
            self.assertIsNone(sys.stdout)
            self.assertIsNone(sys.stderr)

    def test_help_short_write_flush_and_null_redirection_close_failure(self):
        from rangelab.__main__ import main, _silence_failed_stream
        for mode in ("short", "flush"):
            stdout, stderr = MagicMock(), MagicMock()
            stdout.buffer.write.return_value = 0
            if mode == "flush":
                stdout.buffer.write.side_effect = lambda payload: len(payload)
                stdout.buffer.flush.side_effect = OSError()
            with patch("rangelab.__main__.sys.stdout", stdout), patch("rangelab.__main__.sys.stderr", stderr), \
                    patch("rangelab.__main__._silence_failed_stdout", return_value=True):
                self.assertEqual(main(["--help"]), 1)
                stderr.write.assert_called_once_with("rangelab: IO_ERROR\n")
        stdout = MagicMock()
        with patch("rangelab.__main__.sys.stdout", stdout), patch("rangelab.__main__.os.open", return_value=99), \
                patch("rangelab.__main__.os.dup2"), patch("rangelab.__main__.os.close", side_effect=OSError()):
            self.assertFalse(_silence_failed_stream(stdout))
            self.assertIsNone(sys.stdout)

    def test_application_import_capability_boundary(self):
        allowed = {"copy", "json", "os", "re", "argparse", "sys"}
        for file in (ROOT / "rangelab").glob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(alias.name.split(".")[0] in allowed for alias in node.names))
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module.split(".")[0], allowed)


if __name__ == "__main__":
    unittest.main()
