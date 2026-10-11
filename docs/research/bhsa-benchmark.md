# BHSA semantic benchmark research (#10)

Observed against Text-Fabric 13.1.0 and the local ETCBC BHSA `tf/2021` files.
The benchmark precedes parser implementation (#9); its gold is authored independently
of parser prompts and model responses.

## Annotation meaning and execution

Official feature documentation is the authority for the English/code mapping:
[sp](https://etcbc.github.io/bhsa/features/sp/),
[gn](https://etcbc.github.io/bhsa/features/gn/),
[nu](https://etcbc.github.io/bhsa/features/nu/),
[vs](https://etcbc.github.io/bhsa/features/vs/),
[vt](https://etcbc.github.io/bhsa/features/vt/),
[function](https://etcbc.github.io/bhsa/features/function/),
[number](https://etcbc.github.io/bhsa/features/number/).
Requests describe annotations, not inferred temporal meaning or translations.
`number` on words is within a book, not a phrase; morphological `NA` and
`unknown` are ordinary annotated strings, not missing feature values.

Raw loaded feature counts include 73,710 verbs, 121,509 nouns, 6,106 Aramaic
words, and 33,002 proper nouns. The existing conformance search proves that
`clause\n  word sp=verb` yields 73,710 witness pairs. A request to return clauses
needs projection onto column zero and deduplication. Gold must specify returned
columns; raw tuple equality is insufficient to score equivalent query forms.

Native TF remains the executor. Inspecting `tf/search/search.py` and the existing
conformance harness shows why diagnostics must be collected through `_msgCache`,
including quantifier sub-searches, then checked after materializing results.
An invalid `/without/` body can report an error even when the outer executor's
`good` flag remains true. A zero-row erroneous query must never equal an empty gold.

## Coverage, provenance and limits

Include literal high-cardinality annotations, structural relations, conjunction,
negation, integer bounds, empty strings and absent annotations. Literal lexeme and
gloss requests do not claim successful semantic translation. Deliberately separate
ambiguous requests from unsupported prototype semantics. Unsupported does not
mean native TF itself cannot express the request.

Source-file SHA256 hashes pin every feature used by gold, plus `otype`, `oslots`
and `otext`. Native execution and frozen projected-result hashes catch accidental
gold drift. Hashes identify this local source snapshot, not a guessed upstream
revision. BHSA data attribution/license is separate from the repository software
license: [ETCBC BHSA](https://github.com/ETCBC/bhsa),
[dataset PID](https://doi.org/10.17026/dans-z6y-skyh), CC BY-NC 4.0.

The benchmark is public, so a held-out partition is a workflow constraint rather
than secrecy. Split whole semantic families and keep held-out requests/gold out of
parser examples, prompt construction, heuristics and tuning. Evaluation must state
when held-out results have informed further development and then version a new holdout.

## Remote reconciliation

Remote main advanced through #23–#27 while this checkout researched the full
benchmark. Fetched and fast-forwarded to `1fd1993` before finalizing. Reviewed
those PRs and their source/IR/native-equivalence discussions. The 24-case v1
seed and its frozen replay reference remain historical evidence, unchanged.
The complete `nl-tf-v2` supersedes that seed for #9/#11 rather than mutating its
schema or adding duplicate cases to its existing partition. All five original
v1 evaluation requests remain held out in v2, including word adjacency: its
whole family moves to heldout to prevent scope leakage into development.
The new runner reuses the existing diagnostic-aware native conformance harness.
