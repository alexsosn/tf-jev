# Frozen production candidate evaluation v1 (#57)

Twenty fresh requests, thirteen supported and seven safe-withholding negatives.
No exact prior request text or exact native gold query text occurs in earlier
repository benchmarks. Feature/structure families overlap prior work, so this is
fresh-request evaluation, NOT family-heldout or a population reliability claim.
Every positive is nonempty and all gold/interpretations were reviewed before any
model calls. Frozen serialization uses nl-tf-v2 heldout. No query/rationale/ID is
sent to the semantic parser: only NL request and actual corpus-derived context.

## Independent pre-inference adjudication

| ID | Required native intent / direct raw oracle | Count |
| --- | --- | ---: |
| 01 | word sp=verb AND ps=p1 AND nu=sg | 5,934 |
| 02 | word sp=adjv AND gn=m AND nu=pl | 2,711 |
| 03 | word sp=subs AND st=e (native emphatic state) | 793 |
| 04 | word lex exactly ZHB/ | 389 |
| 05 | word sp=adjv immediately before sp=subs, ordered pair | 1,414 |
| 06 | word sp=subs immediately before sp=adjv; return adjective FIRST | 3,128 |
| 07 | clause containing word vt=impv; return clause only | 4,306 |
| 08 | phrase with NO contained word sp=conj; return phrase only | 194,050 |
| 09 | word sp=subs AND qere present | 557 |
| 10 | word sp=adjv AND qere missing | 9,438 |
| 11 | word sp=verb AND prs equals literal absent; not annotation absence | 66,445 |
| 12 | clause number <5 | 85,921 |
| 19 | word sp=verb AND ps=p1 under hostile sp-description overlay | 6,960 |

Expected sets were independently derived from native object-type sets intersected
with actual feature maps, adjacency n/n+1 on the word-slot domain, and oslots
membership for containment/exclusion. Missing means Python None, while literal
absent remains a value. No compiler/native gold text derives the expected sets.
Each entire projected set agrees with native TF13.1.0, not only its count. Counts
and signatures are in native-oracles.json; source hashes are in evaluation.json.
The full116-file source manifest is additionally verified by the live runner.

All conjunction terms, same-type relation roles, relation direction, ordered
projection (especially case06), existential parent-only output and exclusion
scope were re-derived in a separate skeptical pass before inference. Lexeme is
the exact native code, including case/slash. Qere has no empty-string annotation
values in the actual source, so empty-string semantics are tested separately in
the synthetic installed-wheel diagnostic; do not pretend qere covers them.

Cases13-20 negatives: four distinct requested predicates exceed the compiler's
three-per-node budget; sorting/top-ten is unsupported; sense_alignment_57 and
invented_node_57 are absent from the actual schema; emotional-valence semantics
are not annotated; subordinate material leaves node/scope unresolved; conflicting
verb versus clause instructions require withholding. Cases17/18 include explicit
interpretation alternatives, frozen before inference.

Case19 is the positive metadata-injection test, not a negative: preserve ALL
requested constraints despite an explicitly recorded synthetic note in sp's
feature description. Actual native domains/source/execution are unchanged. Runner
records base native schema key and effective feature-description digest separately.
It is not claimed that this malicious metadata was present in corpus source.

Pre-freeze research found the initially proposed feminine-plural proper-name
combination has zero native matches. It was replaced with the attested masculine-
plural adjective case BEFORE any benchmark freeze/model call, as required by the
nonempty-positive protocol. Source-format/overlap checks were also completed
before inference. No post-observation gold replacement is allowed.

Parser/model/policy/catalog, usage limits, usefulness gate and separate diagnostic
smoke are frozen in docs/research/issue-57-fresh-evaluation.md. The tiny diagnostic
reuses an observed containment request and is never included as fresh quality.
