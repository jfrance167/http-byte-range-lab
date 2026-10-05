# HTTP byte-range research — October 5, 2026

At the research milestone, no project implementation/tests existed. No upstream
execution, HTTP target or representation access. Recommend original stdlib normalized single-range model;
PLAN.md defines precise proposed scope and approval gate. Evidence is dated inspection,
not a dependency safety certification or immutable multi-file checkout.

## Reuse and knowledge

Read selected vault Home/Codex Integration and HTTP Precondition Lab completion note.
Narrow searches of relevant project/research/decision Markdown found only the deferred
range proposal, not an existing dedicated interval model. Workspace README/PLAN/STATE
range searches likewise found the precondition proposal; this is not an exhaustive
code inventory. Reviewed precondition PLAN/RESEARCH and actual contracts.py, CLI and
verifier source: exact builtin validation, bounds, whole-document admission, inert
reporting, exclusive outputs and source restoration can be reused after approval.
Cache contract separates metadata storage/reuse; framing README addresses split opaque
records; packet-budget PLAN addresses supplied MTU/header arithmetic. None substitutes
for selected-representation inclusive interval semantics. Keep those projects unchanged.
No relevant existing Graphify graph was found in the bounded inventory; no graph built,
private corpus indexed, shared tool recreated or third-party program executed.
Parent tracked modifications (.gitignore/install_weekly_cron.sh/nmap_scan_report.py)
were inspected by status only and preserved. No repository/branch/stage/commit created.

## Primary specification

Read official [RFC 9110](https://httpwg.org/specs/rfc9110.html), sections 14.1.1–14.4,
13.1.5, 15.5.17 and 17.15 relevant excerpts. Offsets are zero-based/inclusive and
refer to encoded representation octets. Ordered integer ranges can be valid but outside
the supplied length; oversized suffixes clamp. A zero suffix is unsatisfiable; a
positive suffix over empty data is nevertheless classified satisfiable. Range handling
is optional, GET-specific, after ordinary/precondition checks with a 200 baseline.
If-Range mismatch ignores Range rather than causing 412. Advertisement is no promise
of later partial response. Invalid range handling permits server choices. Multiple
overlapping/small ranges can amplify work. Therefore select one normalized range,
explicit server choice and declared prerequisite outcome; do not model raw parsing,
multipart, actual validators or empty-suffix response construction.

## Strongest fit candidate: Werkzeug

Connected GitHub narrower repository search returned
[pallets/werkzeug](https://github.com/pallets/werkzeug); initial broad query returned
irrelevant .config repositories, not useful candidates. Also returned twisted/klein,
whose application-framework scope offers no reason to add another candidate dependency.

Actual [Range source](https://github.com/pallets/werkzeug/blob/main/src/werkzeug/datastructures/range.py)
uses exclusive stops internally, negative starts for suffixes and length clamping.
Development constructor trusts passed ranges, parser validates them, and convenience
length helpers use the first range. Raw suffix -0 is rejected by this parser. Do not
copy that parser outcome into the lab's separate normalized zero-suffix classification.
Range helpers accept other units, so they are not an automatic byte-unit policy boundary.

Actual [Response apply_range](https://github.com/pallets/werkzeug/blob/main/src/werkzeug/wrappers/response.py)
requires GET/status 200/bytes/known nonzero length and matching If-Range; it couples
offset calculation to response state and a wrapper. Zero/unknown length bypasses;
this library choice is not the proposed arithmetic model's satisfiability oracle.
[Dedicated tests](https://github.com/pallets/werkzeug/blob/main/tests/test_apply_range.py)
were discovered from the actual tests directory and read in full: one range, clamps,
too-large start, first of multiple ranges, supplied 304, POST, other unit, zero/unknown
length, strong tag and exact-date If-Range matching. Also inspected Range/ContentRange
parser cases in test_http.py, range roundtrip in test_datastructures.py and range
wrapper behavior in test_wrappers.py. No tests were installed/run or copied into labels.
Guessed test_response.py/test_response_range.py and wrappers directory returned 404;
directory discovery recovered the correct test_apply_range.py, preserving failed reads.

[Manifest](https://github.com/pallets/werkzeug/blob/main/pyproject.toml): 3.2.0.dev,
Python >=3.11, MarkupSafe >=3.0.3 runtime; optional watchdog >=6, additional test/build
tools. Identity/deps reviewed, no artifact install or full dependency/advisory audit.
[BSD-3 license](https://github.com/pallets/werkzeug/blob/main/LICENSE.txt) read completely:
copied code would retain copyright/conditions/disclaimer; binary redistribution carries
notices and endorsement restriction applies. No adoption/copy proposed.

Leading [changes](https://github.com/pallets/werkzeug/blob/main/CHANGES.rst) describe
structured-header APIs, range convenience deprecations and response refactoring;
[issue 3291](https://github.com/pallets/werkzeug/issues/3291) was closed September 27,
2026 and explains prior mixed precondition/range ordering, suffix and outcome concerns.
These are maintenance evidence, not a claim every released version contains changes
or has a vulnerability. Inspected current development source, not a selected stable build.
[CI definition](https://github.com/pallets/werkzeug/blob/main/.github/workflows/tests.yaml)
has CPython 3.11–3.15/3.14t/PyPy and Windows/Mac/Linux, immutable action references,
empty top-level permissions and checkout persist-credentials false. Definitions only;
no upstream run result or independent action-SHA attestation inferred.

## Comparison: aiohttp

[Request http_range](https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_request.py)
parses a single raw range with ASCII/case-insensitive matching into a Python slice;
inclusive requested end becomes exclusive stop, suffix becomes negative start.
[Request tests](https://github.com/aio-libs/aiohttp/blob/master/tests/test_web_request.py)
cover head/mid/open/suffix slices, non-ASCII digit rejection and uppercase units.
Inspected actual [FileResponse source](https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_fileresponse.py):
range conversion is tied to filesystem size/mtime, conditional handling, file opening
and asynchronous sending. Not suitable for adoption into a no-resource-access lesson.
Its malformed-range error and zero-size choices are library behavior, not a universal
invalid-versus-unsatisfiable teaching oracle; no new vulnerability claim made.

[Manifest](https://github.com/aio-libs/aiohttp/blob/master/pyproject.toml) declares
Python >=3.10, dynamic version, aiohappyeyeballs/aiosignal/frozenlist/multidict/propcache/
yarl and conditional async-timeout/typing_extensions; Apache-2.0 AND MIT (vendored
llhttp). Inspected opening Apache2 license clauses, not all component notice obligations;
any adoption would need complete component/license/NOTICE review. No adoption proposed.
Leading CHANGES.rst includes 3.14.3 July 22, 2026 maintenance/security-related corrections;
not a complete advisory check. Actual CI-cd definition covers 3.10–3.15 and multiple
build/test jobs. Empty top-level permissions and scoped job grants are visible, but
several action references are mutable tags; that is a supply-chain review limitation,
not proof of compromise. No upstream CI execution/status was verified.

## Recommendation and uncertainties

BUILD the bounded original standard-library model. Frameworks demonstrate useful
conventions and pitfalls but add response/runtime/dependency capabilities outside this
scope. Hand-known expected cases come from the declared contract and independent tiny
index enumeration, not candidate outputs. source-records.json captures URLs, directory
reported Git blob identities and actual inspected scope. Directory metadata and source
bodies were fetched separately: this is dated source inspection, not immutable artifact
pinning. No Scorecard, full advisory/security audit, upstream pass, live conformance or
verified dependency safety asserted. Firecrawl account access had failed earlier in
this session; connected GitHub and official primary-source web access were available.
No paid Firecrawl call was attempted.

## Local-first draft review

Existing loopback qwen3.5:2b extracted three supplied learning facts. First sandbox
attempt failed with EACCES; error metadata retained in worker-raw.txt.metadata.json.
After app-permitted loopback retry, 5365 ms/55 output tokens, all three sentences
accepted after primary-source review; worker-raw-permitted.txt and metadata retained.
Worker made no security/oracle decisions and generated no code. No new model/service,
remote inference/provider/price probe or paid fallback. Remote free OmniRoute considered
unnecessary because this bounded local extraction succeeded. Laya classification/triage
schemas do not help arithmetic specification. Codex performed source/security judgement.

## Subsequent approved implementation

Coordinator 03:19 checkpoint approved stages2–4. Local implementation/checks are now
recorded in STATE.md/VERIFICATION.md; this research inspection does not become upstream
execution, artifact pinning, live protocol assurance or independent audit. Initial
expectations/contract preserved; fixture authoring correction disclosed separately.
