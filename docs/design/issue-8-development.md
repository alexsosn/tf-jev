# Issue #8 development gates

Read the active issue, #6 research discussion, repository gate documents and
open PR inventory (no overlap). Rechecked official SDK source and current API
and model documentation, then persisted research/design before production code.

RED: `pytest tests/test_jev.py -q` failed collection because BackendError did not
exist before implementing the intended backend API. Implemented the optional
adapter, then initial 31 tests passed through the actual SDK + HTTP MockTransport.
Tests additionally cover schema-derived choices through native TF execution,
scoped logging restoration and explicit alias requests with resolved-model checks.

Opt-in live synthetic two-question smoke passed against jev-1.13.0 using the
existing project key, with no corpus text or credentials in output. This is a
wire-contract check, not evidence of semantic parser quality. Network tests stay
opt-in; ordinary tests use no real backend. SDK retries are exercised by one
429→200 transport sequence without reimplementing retry machinery.

Core-only wheel imports and the SDK-installed Python matrix are CI gates. Full
exact-head tests, independent review/fixes and final CI results are recorded on
the PR after freezing the reviewed commit.
