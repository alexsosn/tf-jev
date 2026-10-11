# Official tutorial examples as benchmark candidates (#10, intake 2)

Researched 2026-10-11 from the **official** [Text-Fabric search guide](https://annotation.github.io/text-fabric/tf/about/searchusage.html) and the [ETCBC/bhsa tutorial notebooks](https://github.com/ETCBC/bhsa/tree/master/tutorial), at upstream BHSA repository commit `4db00e2157915495e1a4d3d57e41223df24775da`. Notebook Git object IDs are pinned separately in `benchmarks/nl-tf-v1/tutorial-candidates.json`. Query examples come from their actual code cells, not hypothetical search strings.

## Critical version distinction

- `tutorial/searchFromMQL.ipynb` explicitly sets `VERSION = "2017"` and loads `ETCBC/bhsa:clone`; e.g. the PP adjective/noun query notebook reports 64 rows **on 2017**, NOT BHSA 2021.
- `tutorial/search.ipynb`, `searchAdvanced.ipynb`, `searchRelations.ipynb`, and `searchQuantifiers.ipynb` load `use("ETCBC/bhsa")` without pinning a dataset version. Their stored result counts are **unversioned historical notebook outputs**, not BHSA 2021 gold counts.
- The official `tf.about.searchusage` primer uses a **hypothetical** corpus (`pos`, `gender`, `sub`, etc.); those feature names must NOT be copied into BHSA cases.

All new examples therefore enter a separate discovery-only candidate fixture, not the held-out or confirmed benchmark. Notebook-reported counts are provenance clues for independent cross-checks, never acceptance expectations. Promotion to pinned gold requires rerunning the exact query on BHSA `tf/2021`, verifying the full source-file manifest, checking native TF diagnostics/result tuples, and writing a reviewed final expected count. Recorded examples distinguish the researched IR subset from explicitly deferred grammar (regexes, `/with/`, `/where/`).

## Source patterns and suitability

- `search.ipynb`: proper nouns in a specified book, feminine plural substantives.
- `searchAdvanced.ipynb`: multi-feature exclusions, present/absent `qere`, signed integer bounds, type-only count. The tutorial's regex examples are outside our current compiler grammar.
- `searchRelations.ipynb`: same-slot verse/sentence, 3-atom ordering, adjacent phrases. This notebook's printed Text-Fabric version is 9.3.2; result counts are not rechecked against TF 13.1.0.
- `searchFromMQL.ipynb`: prepositional phrase + adjective + substantive, with a compound structural query; 2017 counts must be re-derived, not copied.
- `searchQuantifiers.ipynb`: `/where/` + `/have/`, and `/with/` + `/or/`, both explicitly **deferred** in the current compiler. These make concrete unsupported-intent classification probes.

This intake prevents the benchmark from becoming a set of toy morphological predicates but explicitly avoids silently treating historical tutorial output as current gold.

## Provenance and replay

Case entries record original native query, source notebook file + 0-based code cell index, original notebook-reported cardinality, source data version status, English rephrasing, classification and explanation. Notebook Git blobs are pinned to prove provenance. The candidate BHSA 2021 manifest pins every referenced node/edge feature and structural `otype/oslots` file using Git blob SHA-1 from the `tf/2021` Git tree `c7b070bc5e9950371c1f17c183bd9bd57e5e63e2`.

Replaying candidates is opt-in, local, offline, diagnostic-aware and bounded; it emits observed counts without rewriting gold fixture or confirming semantic equivalence. The candidate bank is **discovery-only**; developers must not sample it as held-out evaluation or claim parser quality from it. This intake PR remains partial progress on #10.

## Independent verification plan

RED-first tests cover malformed provenance, mismatched corpus/version, source mutations after loading, skip of unsupported constructs, duplicate IDs, limit overflows, and zero model/network calls. Native tests on the existing synthetic Text-Fabric fixture establish execution/overflow/error semantics. Full BHSA 2021 replay is opt-in (a deliberately downloaded fixture is not available in ordinary CI). Future benchmark work should re-run, independently review semantic paraphrases, and promote cases as a separate, traceable gold revision.
