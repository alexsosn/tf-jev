# Optional ontology integration (#60)

OntologyParser/load_catalog expose the measured metadata path as an explicit
opt-in package feature. Caller-selected XML snapshots can grow without concept/
feature registry edits; native symbols are validated against the actual full
schema. Catalog digest/revision/source/version/schema/dispositions and per-stage
complete/retrieved/omitted context diagnostics are preserved in the result.

[Replay](replay.json): all 14 historical #59 ontology trajectories / 134 actual
model request structures, distributions, statuses and emitted query/projection
reproduce identically with the public parser. There are no new model calls or
fresh quality claim. Private sorted JSON did not preserve mapping insertion order,
so equality is structural rather than original wire-order proof. Original pilot
and its 7/10 results, imperative regression and cost increase remain immutable.

The growing-catalog overflow path is additional resource behavior, tested with
synthetic catalog additions: scope first, then retrieve complete matched-target
sets by request/label tokens, or omit optional descriptions and expose the reason.
No native option is removed. This path is not claimed to improve semantic quality.
#57 remains the fresh usefulness/safety gate; no model/parser default changes.

The [design](../../docs/design/issue-60-ontology-context.md) records RED/implementation
and installed-wheel once-only smoke protocol before inference. No ontoTF package,
legacy release machinery, HTTP ontology fetch or second executor is added.
