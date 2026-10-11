# Independent audit of six BHSA 2021 tutorial-to-gold promotions (#10)

Research date: 2026-10-11. Inputs: upstream five ETCBC/bhsa notebooks pinned in `benchmarks/nl-tf-v1/tutorial-candidates.json`; 2021 native actual query results from `benchmarks/nl-tf-v1/native-observations-2021.json`, whose exact fields were independently compared to pinned GitHub Actions run 38130781486; `src/tf_jev/ir.py`, `src/tf_jev/compiler.py`, `tests/test_compiler.py`, and native `tests/conformance/tf_harness.py`.

**Independent semantic adjudication (proposed 6; all train/development, none evaluation):**
1. `words-all` (`word`, 426590): explicit all-word node type (train). IR = one `Atom("word")`. NL limits this to loaded BHSA; not a claim about every Hebrew Bible recension.
2. `feminine-plural-substantives` (`word gn=f nu=pl sp=subs`, 5992): exact conjunction of BHSA three word features; `subs` is substantive POS, not an unspecified English "noun" in all corpora (development). IR = one word atom with three EQ predicates.
3. `qere-present` (`word qere`, 1892): presence of node feature `qere` regardless of its particular attested value; this is not a search for a literal word called qere (train). IR = `Predicate("qere", PRESENT)`.
4. `qere-missing` (`word qere#`, 424698): absence of the actual `qere` annotation, not the string value `absent` (development). IR = `Predicate("qere", ABSENT)`.
5. `samuel-proper-noun-context` (`book book=Samuel_I\n  clause\n    word sp=nmpr`, 1868): requests **book, clause, word tuples** (not a distinct count of named persons or clauses), in the first book of Samuel (train). IR three atoms joined through `EMBEDS`, source `book=Samuel_I` is an attested BHSA feature value. The query includes containing clause; no claim about proper noun *lexemes*.
6. `same-slots-verse-sentence` (`v:verse\n    s:sentence\nv == s`, 3583): requests verse/sentence *node pairs* with identical slot sets (development). IR links `SAME_SLOTS` and `EMBEDS` to retain the notebook's explicit nesting, even though same slots alone would likely suffice.

**Explicit non-promotions:** `clause-adjacent-phrases` and compound lexical or long-range patterns still require closer examination of redundant structural clauses and full tuple semantics. `dist` may need review of the actual feature's type/domain and integer comparison. Complex multi-negation queries need careful interpretation of `feature#x` and missing values before asserting an English equivalence. A 2017 MQL query actually shifted from 64 to 61 rows on 2021: do NOT promote it without separate rewording and independent adjudication.

**Provenance:** BHSA `tf/2021` corpus commit `4db00e2157915495e1a4d3d57e41223df24775da`, native Text-Fabric 13.1.0. Six original native tutorial queries *already replayed* against the correct data; add the specific feature file pins `book.tf`, `qere.tf` from upstream git tree: `70407385b60568eaeb44dbeb45f3a7dfafd2a6af`, `405b9a7e98dbc85c401a6e9cf7e4978a04bfe2ee`. The pre-existing 7 source files remain pinned. The gold benchmark is **versioned research data**, not publicly demonstrated semantic-model accuracy.

**Strong equivalence gate:** Native *tuple count* alone is insufficient; on pinned real BHSA compile each hand-adjudicated typed IR using the actually loaded TF node/value domains, then compare full sorted native TF result tuples against the original tutorial gold query using the diagnostic-aware TF search harness. If a compiler query differs in tuple ordering or member identity, fail rather than accepting matching counts. This admits only deterministic/typed compiler capability, not correctness of any future model-generated IR.

**Leakage and splitting:** Treat these sourced historical tutorial cases as training/development only, never add to existing evaluation or treat their queries as unseen. The sealed evaluation partition is unchanged. Add later independently authored and held-out examples as separate evaluation data; no parser may use evaluation gold for prompts.

## Reproducible workflow

Research/plan prior to RED tests, then add 6 data cases and typed witnesses. Existing pinned source checks expand from 7 to 9. Run ordinary exact-head Python 3.11–3.13 CI and pinned BHSA replay plus typed-IR/native full-tuple equivalence. Independently cross-check case semantics, result arity and node types against original notebook cells and real compiled query output. Update frozen count-only observation reference to new gold fixture SHA256, keep candidate fixture stable and preserve result distinction. #10 remains open; six cases are not ~100.
