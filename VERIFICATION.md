# Verification — October 5, 2026

Final receipt: reports/verification-cli-final/results.json; adjacent stdout/stderr logs.
Actual command: python tools/verify.py --output reports/verification-cli-final.
Runtime Windows CPython 3.13.7. 11 checks passed; ten current source/test/verifier/
fixture/contract hashes independently recomputed against that receipt with no mismatch.

| Check | Actual result |
|---|---|
| Normal unittest | 32 passed |
| Optimized unittest | 32 passed, including optimized CLI/closed-pipe children |
| Independent tiny index oracle | 704 cases, lengths1–8, finite invented indices only |
| Frozen expected labels | 40 scenarios, 28 supported/12 unsupported |
| compileall | passed |
| Bandit 1.9.4 | zero findings/errors |
| Omit inclusive +1 | 23 assertion failures, frozen labels included |
| Omit suffix clamp | 3 assertion failures, frozen labels included |
| Incorrect first-offset equality | 4 assertion failures, frozen labels included |
| Ignore baseline gate | 5 assertion failures, frozen labels included |
| Exact source restoration | restored; 32 tests passed afterward |
| JSON/Markdown demos | expected exit2; all40 rows; 36290/105679 bytes |

Six explicit narrow fixed-command subprocess exclusions: test B404 import, test B603
run, two test B603 Popen sites; verifier B404 import and B603 run. No application suppression;
scanner stderr contains informational lines, no scan error. Bandit's nosec metric is
not used to count comments; actual scoped comments were inspected.

Interface tests cover whole-input/late-invalid gates, cycle/custom/alias handling,
numeric/depth/node/container/encoded-byte bounds, null/count/provenance and exact field
shapes, parser authority/escaped strings, inert Markdown, input/result immutability,
fresh/alias/existing/missing paths, short/flush/close/cleanup failure seams, actual CLI
exits and stdout closed at four sizes. Output cap tested through honest reporter seam;
not asserted reachable by every valid document. Import inventory checks available
capability only; it is not a sandbox or complete dynamic-security proof.

Original 27-test verifier receipt/logs preserved at reports/verification (before added
complete declaration/schema check and optimized closed-pipe child propagation).
First test run failed fixture-authoring and stdout/harness cases; see
research/FREEZE-CORRECTION.md. Initial contract/expectations frozen before code; five
null inputs corrected afterward with expected/contract bytes unchanged. Original three
artifacts and receipt retained at research/freeze-v1; current corrected receipt at
research/fixture-freeze.json. No implementation-generated expectation replacement.

The coordinator's 03:51 CLI review found defects missed by the earlier self-review:
explicit empty output selected stdout, and diagnostic/argument delivery was unchecked.
The corrections reject empty/NUL paths before access and check help and fixed diagnostics.
reports/verification-cli-final/cli-boundary.json records 24 actual normal/optimized
process checks, including closed stdout/stderr/both, help, errors and valid report delivery.
NUL paths enter main through a controlled JSON wrapper, not impossible NUL OS arguments.
Previous 28-test and intermediate CLI receipts remain preserved as historical evidence.

No live HTTP/representation/body/codec/server/browser/multipart, full conformance,
upstream tests, independent audit, Linux/other-runtime, hosted security/CI or dedicated
secret/history audit performed. Self-review covered own code/fixtures/callers; manual
boundary review pending. Parent/earlier/shared work preserved; no publication.

