# ontoTF context pilot v1 (#59)

Fourteen new natural-language requests frozen before inference: ten supported,
four safe-withholding challenges. Serialization uses nl-tf-v2's `heldout`
partition, but this is a **fresh-request paired pilot**, not family-heldout
validation: morphology/relations overlap previously observed feature families.
No exact request appears in earlier repository benchmarks. No query or rationale
is supplied to the parser/model. The versioned native results are immutable.

The companion bhsa.xml is verbatim from ontoTF commit
4d1112b9c9ec077e3dbf6cd6150b69ac6e53d3b9, path src/tfont/mappings/bhsa.xml,
retrieved from GitHub on 2026-10-20. LICENSE.ontoTF preserves its MIT notice.
Ontology IRIs are referenced, not bundled ontology definitions. Do not substitute
the old published v0.1.1 wheel or local stale checkout for this pinned XML.
Twenty-four exact value records pass membership checks against the full BHSA
schema. The remaining native-only dispositions are excluded from added context;
absence of an exact mapping never removes a native parser option.

## Native-gold independent adjudication before inference

Every positive must preserve every stated annotation constraint and requested
output role. Direct expected sets use only actual native type sets, feature maps
and oslots, independently of the deterministic compiler/native gold query:

| Case | Required meaning / independent expected set | Count |
| --- | --- | --- |
| 01 | word, sp=nmpr AND nu=pl | 36 |
| 02 | word, sp=subs AND gn=m AND nu=du | 224 |
| 03 | word, sp=adjv AND gn=f AND nu=sg | 1,203 |
| 04 | word, sp in {subs,nmpr}; explicit broad noun including both | 154,511 |
| 05 | word, st=c; native state metadata says construct | 39,870 |
| 06 | word, sp=verb AND vt=impv AND ps=p2 | 4,306 |
| 07 | phrase p where oslots(p) intersects word sp=adjv AND nu=pl; output p only | 2,857 |
| 08 | clause c where oslots(c) has NO word sp=prep; output c only | 35,849 |
| 09 | word, lex exactly XKM/; literal case/slash preserved | 138 |
| 10 | word, prs_ps=p3; suffix person, NOT the word's own ps | 24,498 |

All sets are nonempty and have complete projected-result counts and SHA256
signatures in native-oracles.json, verified against native TF 13.1.0 and all
relevant source hashes. The full 116-file source manifest and full-schema key
are rechecked by the live runner, not inferred from the XML version label.
The broad Noun catalog's subs/nmpr links do not license broadening case02.
The ontology's own-word person mappings do not license substituting ps for
prs_ps in case10. Native metadata distinguishes these annotations.

Case11 leaves "marked gender" unresolved (feminine versus an explicit known
gender annotation). Case12 asks aggregation outside the compiler subset. Case13
names a nonexistent annotation checked against full schema. Case14 contains
conflicting verb-word versus all-phrase instructions: require withholding,
not pretending one interpretation was uniquely requested. Ambiguous status
versus unsupported/abstained is reported separately from safe withholding.

The independent adversarial pre-inference pass checked native feature meanings,
all conjunction terms, broad versus narrow category scope, suffix-person scope,
word-type intersections (features can also annotate lexeme nodes), phrase/clause
slot witnesses, negation direction and returned columns. No corrected gold after
model observations is permitted. No inference had occurred when this was written.

See docs/research/issue-59-ontotf-ablation.md for the frozen comparison/gates.
