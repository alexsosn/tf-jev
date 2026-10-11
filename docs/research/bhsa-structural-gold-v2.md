# Research: five further BHSA 2021 tutorial gold candidates (#10)

Date: 2026-10-11. Sources: existing pinned `ETCBC/bhsa` search notebooks (original code cell/query stored in `tutorial-candidates.json`), corpus Git commit `4db00e2157915495e1a4d3d57e41223df24775da`, Text-Fabric 13.1.0, prior *real* corpus replay `native-observations-2021.json`, `src/tf_jev/ir.py`, `src/tf_jev/compiler.py` and the compiler/native test harness.

## Adjudicated intentions (provisional until exact tuple replay)

- `clauses-distance-one`: `clause dist=1`, observed **598** clause tuples. `dist` is a BHSA corpus annotation; the English request must say *feature dist equals 1*, not infer physical length, word gap or syntactic depth.
- `clauses-distance-less-minus-ten`: `clause dist<-10`, observed **86** clauses. Negative integer bound and strict less-than must not be paraphrased as less-or-equal or graph distance.
- `clause-adjacent-phrases`: native `clause\n  phrase\n  <: phrase`, observed **162653** result triples (not distinct clauses). English request must make it clear that two *immediately consecutive* phrases are **in the same clause**; explicit typed relations for both containment and directed adjacency.
- `sentence-clause-phrase-order`: native `sentence\n  c1:clause\n  p:phrase\n  c2:clause\n  c1 << p\n  c2 >> p`, observed **136137** 4-tuples (not sentence cardinality). Requests for clause before phrase and another clause after phrase in a containing sentence. Full clause-vs-phrase ordering is strict; no adjacency/nearest inference.
- `pp-prep-adj-noun`: source is `searchFromMQL.ipynb` **2017**, original native `phrase typ=PP\n  word sp=prep\n  <: word sp=adjv\n  <: word sp=subs`. Notebook reports **64**, but pinned BHSA 2021 actual search returns **61** four-tuples. The natural language refers to sequential adjacent annotated *words* within a PP-typed phrase, not ordinary English "prepositional phrase" when BHSA `typ` differs. The 2017 count must never become 2021 gold.

The five are native execution-valid and have existing count provenance. Their *typed QueryIR representability / tuple identity* is not yet proven by counts. This PR must fail on real TF tuple mismatch, and must not promote a mismatched example. The source `dist.tf` must really be an `int` node feature on clauses, and `typ.tf` an attested categorical feature on phrases; verify via real Text-Fabric API during the native gate. For overlapping phrase boundaries, explicit all-node containment is necessary to prevent false positives leaking over adjacent clause/phrase boundaries. The declared QueryIR relation graph must remain connected.

## Pinned provenance and scope

The current benchmark has 19 total / 12 supported, 5 evaluation examples unchanged. New examples are **train/development only**, retaining original source notebook strings exactly; corpus source-manifest expands from nine to eleven by adding `dist.tf` (Git blob SHA1 `e88470f33af1dd9dc282424f7c17ca17cb4451f3`) and `typ.tf` (`10c075abd4da74088baa7f3675ca56edc09893de`) from the upstream Git tree. Prior source hashes and `otype.tf` SHA256 stay untouched. Candidate discovery records are not modified. Target after five successful promotions: **24 total, 17 supported, 3 ambiguous, 4 unsupported**, with the original 5 evaluation records unchanged.

Failures to probe: `PredicateOp.LT` with a negative bound, invalidly treating `dist` as a string or an unobserved threshold; wrong direction or transitivity in `<:`; accidental tuple projection/duplicate elimination; outer context-only joins increasing cardinality; `typ=PP` domain membership; historical 2017 cardinality reuse; and changed result tuples with unchanged count.

This is a benchmark/typed-IR coverage increase, **not** evidence that a Jev backend can parse any prose. No semantic parser or prompt engineering should use evaluation cases. The goal of #10 is still ~100 and independent withheld evaluation cases; further coverage and true held-out research remain outstanding.
