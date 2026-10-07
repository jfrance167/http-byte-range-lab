# ECC actual-change self-review — October 5, 2026

Applied installed ecc-code-review skill and pinned reviewer checklist. Implementing
agent performed this review; no independent reviewer/native ECC-runtime claim.
Scope: own five application modules, tests, fixed-command verifier, corrected/original
fixtures, frozen contract and documentation; read actual surrounding code and callers.
Parent tracked edits/other projects outside scope preserved; no review publication.

| Finding/correction | Evidence and focused fix |
|---|---|
| P2 enum type boundary | contracts.py _choice: set membership with list/dict enum could throw uncaught TypeError; exact str guard added, malformed enum tests pass. |
| P2 stdout error exit | __main__.py: actual closed stdout reproduced exit120 despite caught flush OSError; failed descriptor redirected to OS null sink, four-size normal/optimized actual children and fixed-error seams pass. Host-descriptor failure disclosed separately. |
| Fixture authoring/harness | Five intended null range inputs retained defaults; independent answers unchanged and old freeze preserved. Closed parent pipe removed from communicate readers. Not an arithmetic label change. |
| Review verification gap | Added exact root/result/declaration schema checks for all40 cases and propagated optimized mode into actual closed-pipe children. |

Current exact locations: contracts.py _choice lines135–138; __main__.py stdout helpers
lines12–66. Historical broken variants are described in LEARNING and freeze correction;
they are not falsely presented as present defects. No unresolved scoped application
finding established after corrections; severity is proportional to local interface impact.

Coordinator 03:51 review exposed two missed P2 CLI defects. Empty output used truthiness
and silently selected stdout; explicit None checks and empty/NUL admission now guard
paths at __main__.py lines98–108. Unchecked stderr and argparse delivery could replace
the chosen exit with shutdown exit120. Checked fixed diagnostics at lines56–66 and
checked help/argument parsing at lines77–88 preserve the intended exits in tested cases.
Failed streams redirect to the OS null sink or detach from Python's stream slots when
redirection fails. Reviewed the actual CLI, surrounding callers, verifier and regression
tests again; 24 recorded actual normal/optimized boundary checks pass. This corrective
review is still implementing-agent self-review, not an independent audit.

Reviewed numerical geometry/empty behavior, whole validation and unsupported priority,
null/count distinction, If-Range/coding provenance, fresh copies, escaped fields, delivery
errors/cleanup, fixed subprocess targets/timeouts, mutation assertions/restoration and
evidence honesty. No credentials/real private data intentionally introduced; this manual
source review is not a dedicated secret/history scan or dependency/advisory audit.

Final 32 normal/optimized/restored tests, 704 independent finite oracle cases, four
assertion-detected mutants (23/3/4/5), compile/Bandit/demos pass; ten receipt hashes match.
Verdict: local approved scope complete, no outstanding scoped finding. Manual review,
live/actual-origin/auth/resources/multipart/conformance/runtime/hosted limits persist;
review verdict grants no merge/deployment/publication authorization.

