# Issue #3 development gates

2026-10-11. Research and plan preceded production code; see
[typed compiler contract](typed-compiler.md) and #2/#4 research.

RED command: `.venv/bin/python -m pytest -q tests/test_compiler.py`.
Observed collection failure: `ModuleNotFoundError: No module named
 'tf_jev.compiler'` (the intended API did not exist). The initial tests already
covered literal sets, integer bounds, all relation operators, edge traversal,
without bodies, exact TF execution, symbol/type attacks and deterministic output.
Implementation then made these tests green. BHSA tests remain opt-in.

The IR represents one predicate per feature; alternatives are a tuple within
that predicate. Multiple predicates on one feature are explicitly rejected,
rather than implicitly interpreting their intended combination. This narrows
#2's merge suggestion without losing its expressible set alternatives.
Two-sided bounds, identity and richer quantifiers remain deferred.

The compiler is pure: schema access is through SymbolSchema, with no TF
execution, backend imports or network. Actual native searches in integration
tests validate results. Production execution/diagnostics are deferred to #11/#13.

Exact-head checks and the separate adversarial review are recorded on the PR,
so adding verification prose does not silently change the reviewed commit.
