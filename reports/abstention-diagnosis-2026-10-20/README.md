# Development-only abstention diagnosis (#46)

**The failure is concentrated in three structural decisions. No safe wording-only
fix is established, so production parser behavior and the no-go remain unchanged.**

Frozen inference source `df65c441bc5e3e2847f44391a01145078a4b5b8d`, Jev 1.13.0,
SDK 0.7.4, native TF 13.1.0, original full BHSA schema and all 116 source hashes.
Only the 52 DEVELOPMENT requests were inferred. The previously observed v2
heldout was not used for any new calls, calibration or experiment selection.
The protocol was committed before measurement. Every case and failed attempt is
retained, with no outcome-driven reruns.

The [trace](trace.json) records positional validated distributions and margins,
static question IDs, completed/failed attempts and returned usage. No raw
request, option description/label, corpus passage, query, prompt or credential
is published. It reproduces the original full schema identity and 51 abstentions
plus one unsupported decision; no query/IR is emitted.

| Stop stage | Requests | Finding |
|---|---:|---|
| Shape | 33 | 32 low-confidence refusals, one correctly unsupported aggregation |
| Node type | 11 | All select the correct word slot type, but probability is .51–.77 |
| Predicate count | 8 | Four of six literal lexeme cases choose two predicates instead of one |

None reaches feature/value selection, relation construction or final compilation.
The shape stage's top choice matches the development construct in 41/52 cases.
Errors are all six containment cases, all four ambiguous-scope cases and the
unsupported regex example. These diagnostic construct labels are derived from
the existing benchmark annotations/native query semantics, never sent to Jev.
They are not new end-to-end quality or calibrated-probability measurements.

Actual native `C.levels` and slot type confirm the 13-option type inventory and
word at position 12. Its winning margin at the 11 type stops is .36–.65, yet the
absolute-probability gate refuses them. Meanwhile four literal count winners are
wrong. This mixture does not justify globally lowering the .80 threshold or
.20 margin: uncertainty and actual planning mistakes both occur.

The initial shape payload contains no corpus inventory or supported predicate
operator list. It asks the backend to distinguish unsupported semantics using
atom/predicate terminology before supplying the relevant capabilities. In
particular, regex is native TF syntax but outside this IR subset. The payload
cannot tell the model that distinction. This is a demonstrable contract gap and
a plausible contributor, not proof that one missing field explains all failures.

The [paired probes](probes.json) use the canonical first request in each of eight
development families, fixed before outcomes, with two repetitions per variant.
All five categories are retained. There are 16 scheduled observations per variant:

| Variant | Correct shape/resolved class | Pass original five-way gate | Correct among gate passes | Errors |
|---|---:|---:|---:|---:|
| Exact control | 10/16 | 6 | 5/6 | 0 |
| Reverse option order, preserve mapping | 10/16 | 6 | 4/6 | 0 |
| Semantic labels | 10/16 | 6 | 4/6 | 0 |
| Plain shape wording | 8/16 scheduled (8/15 returned) | 10 | 8/10 | 1 |
| Request-only state | 8/16 | 5 | 4/5 | 0 |
| Five independent binary classes | 0/16 resolved | n/a | n/a | 0 |

These are isolated shape decisions; **none of the probes constructs or executes
a query**. A correct class or a gate pass is not parser success. Binary outcomes
are independent yes/no probabilities, not a five-way distribution, and no winner
is forced if uncertainty or conflicting positives remain.

Plain wording raises the simple verb example to .97 in both repetitions, but
also raises the wrong atomic classification of the unsupported regex request to
.91–.93. It changes negated containment from the correct exclusion class to the
wrong atomic class (.77–.79). Control repeats for the same verb payload vary from
.69 to .81, straddling the gate. Reversal also changes the negated class from
.69 to .45–.50 without changing its winning category. Decomposition has no yes
probability above .77 and resolves no class at the frozen .80 policy. Confidence
increases alone cannot identify a safer parser. The fixed variant order and two
repetitions do not establish a causal decomposition or statistical ranking.

175 backend calls were attempted: 79 trace calls and 96 probe calls. One plain
containment probe has a sanitized response-contract error and unknown usage;
it was not retried as a fresh observation. Returned input usage is known for
174 calls (87,940 input and 15,518 output tokens). At the same .042 USD/million
input, free output list rate checked for the frozen study, known-returned-usage
cost is **$0.00369348**. Complete model cost is **unknown**, because the failed
call may have consumed tokens and SDK retry/invoice costs are not measured.
The [analysis](analysis.json) explicitly stores null total cost. Shared extraction,
CPU and native corpus-load costs are excluded from model USD.

The 52 original traces and 96 probe records remain byte-identical to the frozen
run. A later diagnostic-only RED/fix distinguishes last validated question from
last attempted question after an error; the original probe error is not rewritten.
No inference, threshold, parser, compiler, schema or benchmark behavior changed.
Tests exercise transparent ParseResult identity and actual tiny native search,
saved-corpus CLI/source gates, hostile label/response and error cases, and every
probe variant through the real SDK's mocked HTTP boundary. Mock tests establish
diagnostic correctness, not semantic quality. Native gold replay of all six
supported first-per-family development representatives validates the construct
reference. Exact-head checks and logically independent review are recorded on
PR #47 before merge.

The evidence justifies a **new research/design gate (#48)** for corpus-aware
structural planning, explicit type roles, semantic feature selection/counting
and development-calibrated stage policies. It does not yet justify a production
parser revision. Any future revision needs RED-first tests and a newly frozen,
independently reviewed evaluation set; the observed v2 heldout is regression
evidence only. The no-default recommendation remains in force.

Reproduce on the frozen source (new report path, paid calls explicitly enabled):

```bash
TF_JEV_LIVE=1 python -m scripts.diagnose_abstention /path/to/bhsa/tf/2021 \
  --max-cases 52 --output /tmp/new-development-diagnostics --live
```

The command has no heldout selector, verifies the complete source inventory
before client setup, and checkpoints completion status without overwriting a
previous report directory. Source/benchmark/code/schema/model versions are in
both immutable JSON reports; [SHA256 manifest](sha256.json) covers the artifacts.
