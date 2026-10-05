# Learning

A requested last offset is inclusive: positions 2,3,4 select three octets. Internal
framework slice stops are often exclusive; translating conventions needs an explicit +1.
An oversized suffix clamps to the representation, while an out-of-bounds first offset
is unsatisfiable. Neither should be confused with reversed invalid endpoints.

Zero selected bytes and unknown count are different. RFC's positive-suffix empty case
has a satisfiable classification without a nonempty inclusive interval; constructing
0..-1 would make a misleading report. Arithmetic alone cannot require a server response.
Encoded representation offsets are not decoded characters or compressed-input provenance.

Two implementation lessons: set membership with an unhashable API enum can raise
TypeError unless exact strings are validated first; full-tree checks alone allow lists.
And Python may retry buffered stdout at shutdown, replacing an intended error exit1 with
120. A tested failed-descriptor null redirection avoids that ordinary closed-pipe path.

The first fixture writer spread null as an object and retained the default range in
five cases. Expected answers exposed three comparisons plus an unsupported-count mismatch;
two global-scope cases hid the authoring error until input inspection. Corrected those
inputs, preserved the old freeze, and kept expected/contract bytes unchanged. The first
closed-pipe harness also tried communicating with a closed reader; set that handle to
None so the test probes child delivery instead of a parent reader-thread failure.

704 invented-index cases supplement known labels without copying the production formula.
Mutation evidence must include expected fixture assertion failures, not just exit1 from
a syntax/import error. Four targeted mutants were caught and exact source restored.

## CLI correction learning

The earlier self-review missed empty-output truthiness and unchecked stderr/argparse
paths. Catching the report error alone does not handle a later diagnostic flush or
Python shutdown retry. Test help, arguments, valid output and errors with stdout,
stderr and both closed before execution; repeat in optimized Python. An empty string
is an explicit invalid path, not the absence of an output option. NUL-path tests must
call main through a controlled wrapper because OS arguments cannot contain NUL.
These lessons come from the coordinator's reproduction and the verified correction.
