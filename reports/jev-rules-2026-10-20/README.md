# Jev and conservative rule baseline: measured no-go

Measured 2026-10-20 (Athens local date), frozen source commit
`3abcf270911798e7414124772b5fe27e5ecbf32c` (see full `package_commit` in JSON), BHSA 2021 / TF 13.1.0,
TypeSafe SDK 0.7.4, Jev **1.13.0**. The exact benchmark hash, 19 pinned source
hashes, full schema identity, package commit, Python version and UTC start are
in each report. Protocol and thresholds were committed before inference;
parser, default thresholds, prompts, rules and benchmark were unchanged after
heldout inspection. This is one run, not a statistical model leaderboard.

**Decision: do not select this Jev pipeline as the default parser.** It emitted
no IR/query for any of the 109 requests. Cheap safe abstention is insufficient
for a usable parser. The rule baseline also fails the heldout usefulness gate.
Keep the compiler/schema usable independently and the backend replaceable.

| Metric | Jev development | Rules development | Jev heldout | Rules heldout |
|---|---:|---:|---:|---:|
| Cases | 52 | 52 | 57 | 57 |
| Supported execution equivalence | 0/44 | 26/44 | 0/42 | 0/42 |
| Safe negative decisions | 8/8 | 8/8 | 15/15 | 15/15 |
| End-to-end success, including safe negatives | 8/52 | 34/52 | 15/57 | 15/57 |
| Strict supported/ambiguous/unsupported classification | 1/52 | 30/52 | 0/57 | 8/57 |
| Native-valid emitted queries | n/a (none) | 26/26 | n/a (none) | n/a (none) |
| Exact native query text | 0 | 0 | 0 | 0 |
| Operational abstention precision | 15.4% | 30.8% | 26.3% | 26.3% |
| Operational abstention recall on negatives | 100% | 100% | 100% | 100% |
| Parse median / p95, seconds | .319 / .893 | .000141 / .000633 | .316 / 1.094 | .0000305 / .0000424 |
| Backend calls | 77 | 0 | 83 | 0 |
| Input / output tokens | 38,720 / 6,810 | 0 / 0 | 45,624 / 7,994 | 0 / 0 |
| Estimated model USD total | .00162624 | 0 | .001916208 | 0 |
| Parser/backend errors | 0 | 0 | 0 | 0 |

The rules' exact text count is zero because the compiler names `n0` and orders
predicates deterministically; all 26 emitted queries are result-equivalent.
Every rule emission was also inspected independently for requested node type,
annotation predicates and output role: **26/26 correct compiled IR structures**
on development. Jev emitted none, so conditional IR precision is **undefined**,
while supported-gold IR recall is 0/44 development and 0/42 heldout. Rules have
26/44 development IR recall and 0/42 heldout. The separate
[intent audit](intent-audit.json) records every emitted/absent structure and
single-reviewer limitations; result equivalence is not silently called IR intent
correctness.

Jev made 108 `low_confidence` refusals plus one explicit unsupported decision.
There were no transport/contract failures. The .80 minimum probability and .20
margin were frozen; they were not lowered to improve these results. Reports
retain reasons, confidence, family, decision/attempt counts, model identities,
usage and timing. They do not retain full distributions or the exact stopping
question; this limits diagnosis of the gate beyond early-abstention evidence.
There is no evidence here that Jev cannot work with a different researched
orchestration; that would require a fresh experiment and uncontaminated test set.

The original local literal audit recalled **6/6** development lexeme values.
A separate [supplementary candidate audit](candidate-audit.json) extends the
post-inference audit to the three pointed-lexeme and three gloss heldout cases:
**6/6 development and 6/6 heldout**. It verifies the same source/schema identity
and calls the unchanged parser's actual candidate routine; no model call or
inference change is involved. The initial live JSON remains byte-identical and
honestly retains its narrower audit scope. Gold is only a comparison target;
only request-derived seeds drive candidate retrieval. Upstream abstention
prevented Jev from visiting these candidate selections during inference.
This establishes availability for these 12 explicit literal probes, not semantic
retrieval recall for paraphrases, translations or arbitrary feature values.
Broader semantic retrieval recall remains unmeasured.

Paired outcomes: rules alone succeed on 26 development requests; neither system
alone succeeds on a heldout request. Heldout has 15 shared safe-negative successes
and 42 shared supported failures. Both systems have zero supported equivalence in
every heldout family; full per-family counts are in JSON. On development, rule
success is POS 10/12, gender/number 10/10 and literal lexeme 6/6; it abstains on
all other constructs. The baseline deliberately targets simple development
patterns, so its development advantage is not a heldout generalization claim.
No comparison with a generative alternative was made.

The frozen heldout targets were >=80% supported equivalence, >=95% safe negative
coverage with zero unsafe emissions, all emitted queries native-valid, <=5%
errors, parse p95 <=10 seconds, and known mean estimated model cost <=$0.001.
Jev meets safety/error/latency/cost targets but fails usefulness. Native validity
is unestablished because it emitted nothing, not a vacuous 100% success. Neither
system is recommended as the default. No task shows a measured Jev quality,
latency or model-cost advantage over these rules. This answers #11/#12 with a
negative prototype result, without recommending the narrow baseline as a broad
replacement.

Prices are [TypeSafe list estimates](https://typesafe.ai/) checked 2026-10-20:
$0.042/million input tokens, free output. All returned usage was complete, but
these are not invoice costs or metered total SDK retry charges. The full measured
run totals **$0.003542448** estimated model usage; the separate one-case
connectivity probe adds $0.000020496 and is excluded from accuracy aggregates.
CPU/memory/corpus-load costs are excluded from model USD. Shared full schema
extraction took 72.72 seconds; native load and extraction are excluded from parse
latencies. Full wall latency includes native execution (rules development p95
1.026 seconds), and system order/cache effects preclude an execution performance
ranking. Zero rule model cost means no model invocation, not free computation.

Reproduce from the measured commit (network calls require both opt-ins):

```bash
TF_JEV_LIVE=1 python -m scripts.measure_comparison /path/to/bhsa/tf/2021 \
  --output /tmp/new-measurements --private-review /tmp/new-private-review --live
```

Both output paths must be new. The private review directory contains only local
candidate query/projection data for intent audit; it is not published. Public
reports contain no request prose, raw query, corpus passage, prompt or credential.
All four system/partition reports are complete; errors/refusals were not retried
as new benchmark cases. Native gold replay and exact-head test/review evidence
are recorded in the PR before merge. TF 13.1.1 compatibility is tracked separately
in #45; the frozen study remains on 13.1.0.
