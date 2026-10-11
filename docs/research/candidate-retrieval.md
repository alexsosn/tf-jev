# Candidate retrieval research — issue #7

Inspected Text-Fabric 13.1.0 loaded `Fs(feature).items()` against BHSA 2021,
filtering with the actual `F.otype.v(node) == "word"`. Independent Counter/grouping
probe (2026-10-11):

| feature | distinct | non-NFC | NFC + casefold collision groups | largest group |
|---|---:|---:|---:|---:|
| lex | 8769 | 0 | 0 | 1 |
| voc_lex_utf8 | 8091 | 3287 | 0 | 1 |
| gloss | 6132 | 0 | 11 | 2 |
| nametype | 10 | 0 | 0 | 1 |

Gloss collisions include `put`/`Put` and `i`/`I`. Prefix `B` matches 451 lex
values, Hebrew `א` matches 816 pointed lexemes, and `king` matches three glosses.
Frequency is attestation count, not evidence of intended meaning. Ranking by
frequency would silently lose rare correct values. Missing annotations do not
become candidates; empty strings remain genuine values.

Exact lookup and NFC lookup recover attested spellings without linguistic
assumptions. Case folding is an explicit caller option, not a generic default:
transliteration capital letters can be significant. Prefix matching is explicit
and lexical only. Neither method translates English into Hebrew. Gloss is a
separate available feature, not automatically a lexeme label or join. Such a
mapping requires schema-grounded parser research (#9). Fuzzy edit distance has
no demonstrated tolerance/recall contract here, so no approximate winner is
invented. Absent values remain no-match.

Use the immutable schema's local inventories and identity-bound handles. No
corpus downloads or backend calls are necessary. Keep candidate strings original;
normalization only affects lookup keys. See the existing decision contract
(`Option` opaque labels, original strings in descriptions) and corpus-schema
research for the 32-option operational budget. Unicode operations use Python
`unicodedata.normalize` and `str.casefold`; normalize again after case folding
because case folding itself need not preserve NFC.

Evaluation: freeze a real-domain lookup benchmark separately from the later NL
semantic benchmark (#10). Measure gold-value inclusion, no-match, overflow and
handoff eligibility separately. An overflow is neither a successful semantic
choice nor an invisible miss. Synthetic native TF domains exercise normalization
collisions, duplicates, empty values, stale handles and untrusted strings.
