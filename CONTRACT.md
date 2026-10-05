# Frozen byte-range teaching contract v1

October 5, 2026; frozen before application source. PLAN.md approved stages 2–4 with
03:19 addendum; counterfactual GET geometry is separate from hypothetical handling.
No raw HTTP, resources or responses. All lengths/offsets/codings/outcomes invented.

## Admission and shape

Root exactly version (exact int 1), cases (1–40 exact list). Case exactly id,method,
baseline_status,representation,range,server_policy,if_range,unsupported_features.
IDs unique 1–64 Unicode scalars without C0/DEL; method ASCII token 1–16 case-sensitive;
baseline_status exact int 100–599. representation exactly length nullable exact int
0–1e9,content_coding ASCII token 1–32,length_basis enum selected_representation_bytes/
decoded_bytes/unknown. ASCII lowercased identity/gzip/br supported, original spelling
preserved; supplied selected-representation octets only, no decode or length observation.

range null absent or exact object unit,kind,first,last,suffix. unit ASCII token 1–32,
bytes case-insensitive. kind closed/open/suffix; respective shape integers first+last,
first alone, suffix alone, all unused fields null. Integers 0–1e9 exact; no bool/coercion.
Reversed closed endpoints are admitted INVALID_RANGE, not invalid document. Suffix 0
admitted UNSATISFIABLE. server_policy honor/ignore, if_range absent/match/mismatch/unknown.
These are assumptions, not actual server capability or validator evaluation.
unsupported_features <=8 unique lower ASCII [a-z][a-z0-9-]* length1–32; any unsupported.
Unknown keys, duplicate JSON keys/IDs, wrong shapes/types/limits invalid.

API concrete builtins only; explicit cycles invalid before serialization, repeated
acyclic aliases allowed within aggregate limits. Complete tree and all cases validated
before semantic output, even ignored/unsupported fields. 65536 UTF-8 input bytes,
262144 UTF-8 output bytes, depth8 root1, 5000 nodes, per-container100, strings256 before
field limits, keys64, numeric token10 decimal digits. Reject floats/constants/C0/DEL/
surrogates/custom types/oversized numbers, no normalization/truncation/wrap.
Lexical depth bound before stdlib JSON authority; no custom syntax parser. API encoded
byte bound uses compact canonical separators solely as an admission measure, not JCS.

## Scope and geometry

Global reasons sorted lexically: UNSUPPORTED_FEATURE, UNSUPPORTED_UNIT (nonbytes only
if range present), UNSUPPORTED_LENGTH (null), UNSUPPORTED_LENGTH_BASIS (not selected),
UNSUPPORTED_CODING (not identity/gzip/br case-insensitively). Any causes status UNSUPPORTED,
math UNKNOWN_CONTEXT, handling UNSUPPORTED_CONTEXT, interval/count/status/header null,
If-Range UNKNOWN_CONTEXT, even absent Range or bypassed baseline. This is an explicit
conservative lab scope, not a judgement that a real server must evaluate an absent Range.

Without global scope reason, geometry ignores actual method/handling: absent=>ABSENT,
interval/count null. Closed reversed=>INVALID_RANGE,null/null. Closed/open a>=N=>
UNSATISFIABLE,null/0. Otherwise closed [a,min(b,N-1)] count last-first+1; open [a,N-1]
count N-a. Suffix0=>UNSATISFIABLE,null/0; suffix>0,N>0=>[max(0,N-s),N-1],min(s,N).
Suffix>0,N=0=>SATISFIABLE_EMPTY,null/0; no 0..-1 interval. Nonempty math SATISFIABLE.
Derived count and exclusive conceptual stop <=1e9; never real/error-body length.

## Handling/trace priority

After global scope, informational baseline <200=>UNSUPPORTED_INFORMATIONAL_BASELINE,
handling same, status/header null, geometry retained, If-Range UNKNOWN_BASELINE even
when absent. All other baselines are supplied completed outcomes, not origin evidence.
Subsequent first matching handling gate:

| Gate | Handling and sole reason | hypothetical_status | content-range |
|---|---|---|---|
| range absent | NO_RANGE | baseline | null |
| method != exact GET | IGNORE_METHOD | baseline | null |
| baseline !=200 | IGNORE_BASELINE | baseline | null |
| server_policy ignore | IGNORE_SERVER_CHOICE | 200 | null |
| if_range mismatch | IGNORE_IF_RANGE | 200 | null |
| if_range unknown | UNSUPPORTED_IF_RANGE | null | null |
| invalid math | IGNORE_INVALID_LAB_POLICY | 200 | null |
| empty satisfiable math | UNSUPPORTED_EMPTY_SUFFIX_HANDLING | null | null |
| unsatisfiable math | REJECT_UNSATISFIABLE_LAB_POLICY | 416 | bytes */N |
| nonempty satisfiable math | HONOR_SINGLE_RANGE | 206 | bytes first-last/N |

Result UNSUPPORTED exactly for handling names starting UNSUPPORTED; otherwise SUPPORTED.
The invalid/unsatisfiable policies are declared choices, not mandatory HTTP responses.
Positive empty suffix may be ignored by an earlier gate with known handling, never
fabricates header/416 in the honor path. Whole positive-length range can model 206.

If-Range state after global/informational gates: absent always ABSENT; otherwise range
absent=>IGNORED_NO_RANGE; nonGET=>IGNORED_METHOD; baseline!=200=>NOT_REACHED_BASELINE;
serverignore=>IGNORED_SERVER_CHOICE; reached match/mismatch/unknown=>PASS/FAIL/UNKNOWN.
Empty/invalid math does not retroactively erase reached If-Range trace.

## Results and delivery

Root report exactly version,results,assumptions. Each result exactly id,status,
reason_codes,math_state,interval,byte_count,handling,hypothetical_status,
hypothetical_content_range,if_range_state,declaration. interval null or {first,last}
inclusive. declaration is a fresh complete inert input case without id, not caller alias.
Fixed assumptions distinguish geometry/normal/precondition baseline/coding/If-Range/
policy from any actual response, auth, decoding, resource read/mutation or conformance.
No raw headers/URL/path/body admitted. Every unknown null has a reason; no false stand-in.

CLI file input with bounds read+1; no overwrite/input-output alias, fresh exclusive file
output, fixed validation/I/O errors. Exit0 all supported (including hypothetical
rejection/ignore),2 any unsupported,1 admission/delivery; argparse errors separately2.
No semantic partial report. Short/flush/close fresh-file errors attempt own-new-file
cleanup and disclose cleanup failure. Stdout can be partially delivered; failure exit1.
JSON ASCII escaping; Markdown each derived character encoded as numeric entity and
all fields rendered, fixed key names. Reporter helpers take evaluated records only.
No hostile filesystem race, special-file, hard-resource, atomic stdout/durability claim.
