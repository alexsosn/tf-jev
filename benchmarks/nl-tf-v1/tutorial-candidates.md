# Official tutorial candidate bank — discovery only

These 18 examples were adapted from the [official Text-Fabric search documentation](https://annotation.github.io/text-fabric/tf/about/searchusage.html) and the [ETCBC/bhsa notebooks](https://github.com/ETCBC/bhsa/tree/master/tutorial) as of upstream commit `4db00e2157915495e1a4d3d57e41223df24775da`.

**14** examples use native constructs intended to be expressible in tf-jev's researched compiler subset. **4** deliberately use unsupported constructs, including regular expressions and `/where/`/`/with/` quantifiers, for later abstention tests. Each entry records its notebook and original *zero-based* code-cell index, upstream Git blob SHA-1, original native query, novel English request, and historical result count.

**No entry is BHSA 2021 semantic gold yet.** All 14 in-scope native queries have now been executed on pinned BHSA 2021 via the [replay workflow](../../.github/workflows/bhsa-replay.yml), and the native-only observed counts are frozen in [native-observations-2021.json](native-observations-2021.json). In particular, the 2017 tutorial's PP adjective-noun pattern gives **64** rows historically but **61** on BHSA 2021. This native observation does not yet establish that each English description is semantically equivalent to its query.

 The `searchFromMQL.ipynb` notebook explicitly used **BHSA 2017**; the other tutorials do not pin a BHSA dataset version and include notebooks executed under older Text-Fabric versions. Notebook result totals must not be used as 2021 acceptance thresholds, and the English requests need independent linguistic review for equivalence.

## Run

```sh
python -m scripts.nl_candidates
python -m scripts.nl_candidates --corpus /path/to/ETCBC/bhsa/tf/2021
```

Only the second command executes native TF search, requiring a local, user-provided corpus. The tool first verifies Git blob hashes of all 16 relevant source files from ETCBC/bhsa `tf/2021` and rejects data drift. It then executes only in-scope candidates, with diagnostic handling and an explicit overflow limit. Its JSON observations include computed row counts, notebook-reported rows, and whether they happen to agree. Agreement by itself is *not* gold certification. No corpus text, tokens or credentials are transferred to a model.

To promote: independently audit the example's original notebook query and NL paraphrase, confirm that the QueryIR can compile an equivalent query, rerun full native TF 13.1.0 over the pinned BHSA 2021 data (including corpus provenance and effective-load invariants), record fresh count and preferably result signature, then add a unique case to the frozen split-aware gold catalogue. Do **not** expose the held-out evaluation split while developing parser behavior.

All original benchmark English descriptions are new. Underlying BHSA data are [CC BY-NC 4.0](https://github.com/ETCBC/bhsa#license); attribute the Eep Talstra Centre for Bible and Computer and [dataset DOI](https://doi.org/10.17026/dans-z6y-skyh). The notebook source is cited, not redistributed wholesale.
