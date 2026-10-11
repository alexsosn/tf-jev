# Design: five multi-relation and integer-feature gold witnesses

Extend the existing `benchmarks/nl-tf-v1/bhsa-2021.json` case list (format 1 unchanged) by copying exact five pinned official notebook queries and independently observed 2021 counts. Improve the user requests to specify output **tuple arity**, corpus feature meaning and adjacency scope. Add all five to the existing immutable, explicitly authored `PROMOTED_IR` dictionary (not a template-to-IR parser; no free-form TF from model). Keep all prior cases and each of the original five evaluation cases unchanged.

Typed witness relations:
- `dist=1`: one clause atom with `Predicate("dist", EQ, (1,))`.
- `dist<-10`: one clause atom with `Predicate("dist", LT, (-10,))` (comparison threshold may be unobserved).
- `clause-adjacent-phrases`: [clause, phrase1, phrase2], `EMBEDS(0,1)`, `EMBEDS(0,2)`, `ADJACENT_BEFORE(1,2)`.
- `sentence-clause-phrase-order`: [sentence, clause1, phrase, clause2], `EMBEDS(0,1/2/3)`, `BEFORE(1,2)`, `AFTER(3,2)`.
- `pp-prep-adj-noun`: [PP phrase, prep word, adjv word, subs word], `EMBEDS(0,1/2/3)`, `ADJACENT_BEFORE(1,2)`, `ADJACENT_BEFORE(2,3)`.

**Critical acceptance:** These are proposed mappings; native Text-Fabric 13.1.0 must prove full result tuple equality for every compiled witness versus original notebook query. If a witness has different tuple meaning or exceeds memory/row limits, fix the mapping or **do not promote** it. Do not replace equality with count checks.

Add `dist.tf` and `typ.tf` to strict source manifest, update synthetic manifest fixtures, and add RED-first assertions for (1) new gold split/count/native queries, (2) exact whitelist of reviewed promotions, (3) finite typed IR constraints and directionality, (4) absence of held-out leakage. The existing `validate_promotions()` in the full pinned native replay gates complete tuple equality; unchanged `scripts.nl_candidates` continues to replay all 14 in-scope cases. Native source features must be backed by real corpus data. Add a small opt-in assertion in native gate for `dist` integer data type.

After exact-head native run, take the literal `sha256sum` of revised gold JSON from CI logs, update only `gold_fixture_sha256` and `gold_checked` in `native-observations-2021.json` (keep all 14 per-candidate observations unmodified), rerun all gates. Run Python 3.11–3.13 quality and distribution. A logically independent, skeptical review must inspect actual original notebook cells, source tree Git blobs, exact native IR compiled templates and run outputs before merge.
