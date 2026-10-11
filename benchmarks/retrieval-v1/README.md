# Retrieval lookup benchmark v1

Source: [ETCBC/bhsa](https://github.com/ETCBC/bhsa), TF data version 2021,
Data license: [CC BY-NC 4.0](https://github.com/ETCBC/bhsa#license).
Attribution: Eep Talstra Centre for Bible and Computer, VU University Amsterdam,
[dataset identifier](https://doi.org/10.17026/dans-z6y-skyh).
Small attested annotation-value excerpts only; these retain the data license,
separate from this repository's software license.
The fixture is separate from the NL benchmark planned in #10. It measures local
literal retrieval, **not semantic understanding**, model accuracy or translation.

Frozen 2026-10-11 from loaded TF 13.1.0 raw word features. For each of lex,
voc_lex_utf8 and gloss, choose distinct raw strings at sorted indices
0, floor(N/4), floor(N/2), floor(3N/4), N-1; query original, NFC, NFC+casefold.
Add one absent string per feature, three prefixes, and a real Put/put gloss
collision. Gold preserves original code points. Expected matching sets/counts
are independently recomputed from raw TF items during the test, never from
schema retrieval inventories. No holdout/semantic generalization is claimed.

Run:

```sh
TF_JEV_BHSA_DIR=/path/to/ETCBC/bhsa/tf/2021 .venv/bin/python -m pytest tests/test_retrieval_bhsa.py -q -s
```

Output reports cases, gold values, gold included in the retained budget, no-match,
overflow and handoff eligibility. Total recall and eligible recall must be
considered separately: overflow can drop gold and always blocks model handoff.

For each prefix the gold is the last matching raw value in code-point order,
so broad-prefix misses are deliberately exercised. The JSON records source-file
SHA256 for otype and all three features; evaluation fails on source drift.
Measured with TF 13.1.0: 52 cases, 50 gold values, 48 retained (96%); three no-match,
two overflow; 47 eligible cases retaining all 48 eligible gold values (100%).
Both omitted gold values belong to overflow cases; handoff is blocked for both.
