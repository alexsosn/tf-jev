# Plan: typed-IR witnesses for last three tutorial candidates

Research → RED unit tests → immutable native gold/pins → typed IR implementation → exact-head CI/TF native execution → adversarial review → merge; no hidden mutation of canonical v2 benchmark.

- `complex-verbal-negations`: one `Atom("word")`, `sp=verb` EQ plus `vs#qal`, `vt#infc|infa|ptca|ptcp`, `ps#p3`, `nu#sg`, `gn#m` NE with one set of VT values. Native feature absence is governed by TF semantics and compared on actual data.
- `object-clause-first-lexeme`: three atoms [verse, clause(`rela=Objc`), word(`lex=">CR"`)], two `EMBEDS` links and `SAME_START` from clause to word.
- `complex-predicate-object-lexemes`: five atoms [clause, phrase(`function` EQ (`Pred`,`PreC`)), verb word(`sp=verb`, `vs=hif`, `lex=QWM[`), phrase(`function=Objc`), word(`lex=BRJT/`)]. Four `EMBEDS` relations, no unrequested order.

Extend v1 gold JSON from 24 to 27 with exact original query text and 2021 observations; train or development only. Reuse five pinned blob SHA values from *upstream candidate fixture* and add to `PINNED_FILES` and synthetic manifest tests. Existing original held-out cases unchanged. Refresh the native-only reference's `gold_checked` to 20 and gold JSON SHA256 from the **actual GitHub Actions sha256sum**, not guessed. Do not modify candidate observations or v2 data.

RED tests first assert 27 cases, the exact three new IR witnesses and signed/lexical operators, 16-file pinset, source/candidate provenance. The real-BHSA workflow compares **full native result tuples** for all 14 manually reviewed typed witnesses; simple count equality is insufficient. Fix failures only after reading CI logs, no review/merge until exact-head Python 3.11–3.13, distribution, real BHSA v1 replay, and complete v2 development/heldout replay all pass. Independent review re-reads actual source notebook code cells and pinned tree, not just the implementer plan.
