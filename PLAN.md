# HTTP byte-range lab — proposed plan

October 5, 2026. **Stages 2–4 approved at the coordinator's 03:19 checkpoint.**
Tier 3 portfolio workflow with a bounded offline arithmetic contract. Authorization:
coordinator SUCCESSORS.md October 5 02:52 under Jake's directly verified overnight
mandate. Same sole writer chat 01a10a38-51f7-78a0-be08-65aefc676c4c; separate directory.
Cutoff October 6, 08:00 Eastern. Preserve earlier projects, parent Git and shared tooling.

## Problem, success and recommendation

Teach how normalized single-range requests map to inclusive representation-byte
intervals, and why that arithmetic alone does not force a particular HTTP response.
Success: hand-known boundary examples, separate arithmetic/handling fields, honest
empty and unsupported cases, bounded input/output and no real representation access.

Recommend BUILD an original Python 3.11+ standard-library pure model plus JSON/Markdown
CLI. Reuse reviewed admission/report/fresh-output/verifier patterns from Jake's MIT
precondition/cache/CORS labs after reading their source, without changing them.
Inspect RESEARCH.md and research/source-records.json for actual candidate comparison.
Do not install/fork Werkzeug or aiohttp for this arithmetic lesson. No runtime dependency
is necessary; this is a fit decision, not a claim that dependency count proves security.

Alternative: parse raw Range/If-Range fields and generate multipart responses. That
requires grammar/combination/validator/media-boundary/transport behavior and introduces
amplification and resource costs. Defer it, together with actual file slicing and
response generation. Earlier precondition, cache, framing and packet-budget labs retain
their own scope; this lab neither imports their decisions nor claims their functionality.

## Proposed exact input contract

Root: exactly version (exact integer 1) and cases (list of 1–40 records). Case: exactly
id, method, baseline_status, representation, range, server_policy, if_range,
unsupported_features. Unique IDs 1–64 scalar characters without C0/DEL/surrogates.
method: ASCII token 1–16, case-sensitive; only exact GET uses Range. Other valid tokens,
including HEAD/POST/lowercase get, yield a declared-method ignore result, not proof
that any actual origin recognizes or authorizes the method. baseline_status: 100–599.
This is the supplied final status after normal/precondition checks, before Range.
No automatic execution/import of the precondition lab; caller owns that assumption.

representation: exactly length (nullable exact integer 0–1e9), content_coding (ASCII
token 1–32), length_basis (selected_representation_bytes, decoded_bytes or unknown).
Support identity/gzip/br metadata with selected_representation_bytes and known length.
The supplied length always counts the selected encoded representation's octets;
identity just means no coding. No compression, characters or real payload is observed.
Unknown length/basis/other coding is explicitly unsupported; do not substitute zero.

range: null means absent; otherwise exactly unit, kind, first, last, suffix.
unit: ASCII token 1–32; bytes comparison case-insensitive, original spelling preserved
as inert provenance. Other units are outside this lab rather than treated as bytes.
kind: closed/open/suffix. Closed requires first/last integers and suffix null; open
requires first integer with last/suffix null; suffix requires suffix integer and
first/last null. All integers exact 0–1e9 (bool/float/coercion rejected).
Closed last < first is an admitted *invalid range*, separate from malformed JSON/schema
and from valid unsatisfiable ranges. Suffix zero is admitted and unsatisfiable, not
silently rewritten into an open range. These normalized records are not raw HTTP syntax.

server_policy: honor or ignore, an explicit invented choice; neither is observed.
if_range: absent/match/mismatch/unknown, a supplied outcome only. No raw tags/dates,
strong-validator judgement, parser or comparator. unknown is unsupported if reached;
absent Range/non-GET/baseline gate/server ignore do not evaluate If-Range.
unsupported_features: 0–8 unique lower ASCII names [a-z][a-z0-9-]*, length 1–32.
Any present feature (e.g. multiple-ranges, partial-put, multipart) is unsupported.
Unknown object keys, conflicting shape, duplicate JSON keys/IDs and bad values invalid.

Whole document validation before any result, including later/ignored/unsupported cases.
Proposed limits: 65536 UTF-8 input bytes, 262144 output bytes, depth 8 root=1,
5000 nodes, each container <=100 items, every string <=256 before field bounds,
integer numeric tokens <=10 digits; reject floats/constants, controls, invalid Unicode.
Concrete builtin dict/list/str/int/bool/null API only; no generators/custom methods.
Use reviewed lexical depth admission then stdlib JSON syntax/hooks, not a new parser.
No integer truncation/wrap; derived count/stop never exceeds 1e9 under supported bounds.

## Arithmetic and handling are separate

For each in-scope non-null bytes range and known length N, compute math regardless
of whether a later hypothetical handling gate ignores it:

Math classification means the counterfactual GET byte-range geometry over the supplied
length; it is not a Range applicability verdict for the actual declared non-GET method.

| Form | Math classification and inclusive interval |
|---|---|
| Closed a..b with b<a | INVALID_RANGE, no interval/count |
| Closed/open with a>=N | UNSATISFIABLE, no interval, byte_count=0 |
| Closed a..b with a<N | SATISFIABLE, [a,min(b,N-1)], count=last-first+1 |
| Open a with a<N | SATISFIABLE, [a,N-1], count=N-a |
| Suffix s=0 | UNSATISFIABLE, no interval, count=0 |
| Suffix s>0 and N>0 | SATISFIABLE, [max(0,N-s),N-1], count=min(s,N) |
| Suffix s>0 and N=0 | SATISFIABLE_EMPTY, no nonempty interval, count=0 |
| Absent Range | ABSENT, interval/count null |

SATISFIABLE_EMPTY preserves the standard's positive-suffix classification without
fabricating an invalid 0..-1 Content-Range. It is not classified as unsatisfiable.
byte_count describes selected arithmetic bytes, never an error body's length.

Handling priority, after common validation and global scope checks:
1. Unsupported features/unit/length basis/coding/unknown length: UNSUPPORTED_CONTEXT;
   math UNKNOWN_CONTEXT and interval/count/handling status fields null. This conservative
   lab scope applies even when a supplied baseline would bypass Range; no protocol verdict.
2. Informational 1xx baseline: unsupported completed-baseline context. Math can remain
   known, but handling/status/content-range unknown; never claim completed bypass.
3. Range absent: NO_RANGE with supplied completed baseline, no Content-Range.
4. Method other than exact GET: IGNORE_METHOD with supplied baseline, no Content-Range.
5. Completed baseline other than 200: IGNORE_BASELINE with supplied baseline, no
   Content-Range, including declared 304/412/403. No reinterpretation as success/auth.
6. server_policy ignore: IGNORE_SERVER_CHOICE, hypothetical 200, no Content-Range.
7. if_range mismatch: IGNORE_IF_RANGE, hypothetical 200; unknown: UNSUPPORTED_IF_RANGE
   with null hypothetical status; absent/match proceed. Trace state NOT_REACHED/ABSENT/
   IGNORED/PASS/FAIL/UNKNOWN as appropriate, frozen in Stage 2.
8. INVALID_RANGE: IGNORE_INVALID_LAB_POLICY, hypothetical 200, no Content-Range. This
   is one permitted modeled choice; do not assert actual servers cannot reject it.
9. SATISFIABLE_EMPTY: UNSUPPORTED_EMPTY_SUFFIX_HANDLING, no hypothetical status/header;
   arithmetic retained. A declared server-ignore path above still has known handling.
10. UNSATISFIABLE: REJECT_UNSATISFIABLE_LAB_POLICY, hypothetical 416, explanatory
    Content-Range bytes */N; SATISFIABLE: HONOR_SINGLE_RANGE, hypothetical 206,
    explanatory bytes first-last/N (even whole positive-length representation selected).

Nothing sends a response; hypothetical 200/206/416 are consequences of supplied lab
policy, not mandatory origin outcomes. Accept-Ranges advertisements are not inferred.
Reports must preserve independently known arithmetic on handling-only unsupported cases
without portraying unknown handling as a tested real response.

Result fields frozen in Stage 2: id,status (SUPPORTED/UNSUPPORTED), reason_codes,
math_state, interval (null or {first,last}, inclusive), byte_count, handling,
hypothetical_status, hypothetical_content_range, if_range_state, assumptions.
Known input context reported inertly; no raw request/body/path/URL. Unknown fields null
with explicit reasons, not false. CLI exit 0 for fully supported report (including
modeled ignores/rejections), 2 if any unsupported result, 1 admission/I/O failure;
argument errors separately 2. No semantic partial output. JSON ASCII-escaped; Markdown
derived text numeric-entity escaped. Fresh-file output only, no overwrite/alias,
short/flush/close/cleanup failures fixed; stdout failures nontransactional and exit 1.
Host paths/process/special files and hostile filesystem races outside isolation claims.

## Threat model and limits

Untrusted local synthetic JSON may seek allocation exhaustion, numeric/type confusion,
hidden invalid fields behind early gates or report-content injection. Bound admission
before and after parsing, exact types and full validation, bounded derived arithmetic,
escaping and fixed errors mitigate those interface risks. No network/server/filesystem
resource boundary is enforced by the math. Supplied length, coding, final baseline,
If-Range outcome and server choice are assumptions, not trusted evidence about an origin.
No real requests/files/content slicing, network probes/traffic, response/multipart
generation, compressed decoding, resource mutation, cache merging, resumable transfer
correctness, authorization/authentication, performance/DoS immunity or RFC conformance.

## Stages and definitions of done

1. Research/plan (current, complete): inspect local/vault reuse, connected GitHub actual
   candidate source/tests/license/maintenance/deps/CI and official specification.
   Save this plan, research/source evidence and knowledge milestone; await approval.
2. Contract/oracle freeze (depends on approval): exact trace priority/null/status/shape
   and >=32 hand-known scenarios before code. Record bytes/hashes. Include length 0/1,
   one-byte/equality/one-past, clamping/open/suffix 0/1/N/>N, reversed ranges, caps,
   casing, encoded-basis mismatch, each handling gate, absent/unknown If-Range,
   invalid trailing case behind ignored/unsupported paths and output punctuation.
3a. Validation + pure arithmetic/handling (depends on 2): small coherent library/tests
   with independent labels and tiny invented-index enumeration (N=1..8 only), no
   representation arrays/files/real slicing. Verify exact interval/count and context
   gating independently; normal/optimized tests, no implementation-mirroring oracle.
3b. CLI/reports (depends on 3a): bounded API, inert fields, input immutability, fresh
   output/alias, unsupported/error exits, closed stdout and short/flush/close seams.
4. Review/docs (depends on 3a/3b): assertion-detected +1-count omission, suffix-clamp,
   first-offset boundary and baseline-gate mutations; exact restoration and passing
   affected tests. Compile, available Bandit with only justified narrow exclusions,
   ECC actual-code self-review/fixes and affected reruns. Save runtime/hash receipt,
   README, security model, MIT/attribution/AI disclosure, STATE/DECISIONS/LEARNING and
   verified Obsidian results. Manual review before any merge/deployment, neither
   authorized here; no new repository/publication/hosted security setup.

## Initial independent hand examples (not generated expectations)

Default: GET, baseline 200, honor, If-Range absent, known selected-representation length.

| N | Form | Arithmetic | Modeled handling |
|---|---|---|---|
| 10 | closed 2..4 | [2,4], 3 bytes | hypothetical 206, bytes 2-4/10 |
| 10 | closed 7..99 | [7,9], 3 | hypothetical 206, bytes 7-9/10 |
| 10 | open 9 | [9,9], 1 | hypothetical 206 |
| 10 | open 10 | unsatisfiable, 0 | hypothetical 416, bytes */10 |
| 10 | suffix 12 | [0,9], 10 | hypothetical 206, not invalid |
| 10 | suffix 0 | unsatisfiable, 0 | hypothetical 416, not open 0 |
| 10 | closed 7..6 | invalid, null | chosen ignore, hypothetical 200 |
| 1 | closed 0..0 | [0,0], 1 | hypothetical 206 |
| 0 | open 0 | unsatisfiable, 0 | hypothetical 416 under declared honor policy |
| 0 | suffix 1 | satisfiable-empty, 0 | unsupported handling, no invented range |
| 10 | closed 2..4, baseline 304 | [2,4], 3 | ignored baseline, supplied 304 |
| 10 | closed 2..4, If-Range mismatch | [2,4], 3 | ignored If-Range, hypothetical 200 |
| 10 | closed 2..4, server ignore | [2,4], 3 | ignored choice, hypothetical 200 |
| 10 | closed 2..4, HEAD | [2,4], 3 | ignored method, supplied 200 |
| 10 | closed 2..4, gzip | [2,4], 3 encoded bytes | same math; no decoding |

## Worker and open decisions

Existing qwen3.5:2b extracted three supplied learning reminders after app-permitted
loopback retry: 5365 ms, 55 output tokens. All three reviewed/accepted. First sandbox
attempt EACCES retained separately. No retry loop, generated code or remote draft.
Security/schema/oracle decisions kept with Codex; remote OpenRouter via OmniRoute
considered unnecessary because bounded local draft succeeded. No remote readiness
probe, pricing-dependent call, new service, provider change or spending.
Laya tested classification/triage schemas do not help interval specification here.
Coordinator must approve concrete stages before implementation; especially review
empty-suffix unknown handling, invalid-range ignore policy and independent math reporting.

## Approved implementation addendum — October 5 03:19

Stages 2–4 including 3a/3b approved under Jake's directly verified delegated plan/start
authority. Freeze null-Range/global unsupported priority, informational-baseline unknown
handling while preserving independent geometry, satisfiable-empty and server-ignore
distinction. Coding metadata names ASCII case-insensitive; original token preserved.
Exact-builtin API rejects cycles/custom types and fully validates late fields. Freeze
>=32 independent cases and exact reasons/trace before code. Four assertion-based mutants,
restoration, normal/optimized/actual CLI checks, ECC/SAST/docs/vault required. No new
repository/dependencies/requests/resources/slicing/response emission/network/multipart.
This supersedes the original planning-stage approval-pending wording above.
