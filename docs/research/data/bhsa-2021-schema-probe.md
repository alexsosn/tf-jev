# Schema probe: `BHSA` (2021)

- text-fabric 13.1.0; written 2021-12-09T14:23:29Z
- content sha256 of *.tf: `226a3ce721cafb5de92130a41b77d2b968112ae29f633c6a983bbcb84ebd11d0`
- metadata-only discovery 4.0s; loading all features 14.9s
- slot type `word`, max node 1446831
- object types: `book`, `chapter`, `lex`, `verse`, `half_verse`, `sentence`, `sentence_atom`, `clause`, `clause_atom`, `phrase`, `phrase_atom`, `subphrase`, `word`

## Node features per object type

| feature | type | dtype | distinct | bucket | no value | empty str | non-NFC | needs escape |
|---|---|---|---:|---|---:|---:|---:|---:|
| `is_root` | `clause_atom` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |
| `language` | `lex` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |
| `language` | `word` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |
| `languageISO` | `lex` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |
| `languageISO` | `word` | str | 2 | 1-8 | 0 | 0 | 0 | 0 |
| `det` | `phrase` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `det` | `phrase_atom` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `dist_unit` | `clause` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `dist_unit` | `phrase` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `dist_unit` | `phrase_atom` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `kind` | `clause` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `label` | `half_verse` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `mother_object_type` | `clause` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `mother_object_type` | `subphrase` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `prs_nu` | `word` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `rela` | `phrase` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `suffix_number` | `word` | str | 3 | 1-8 | 0 | 0 | 0 | 0 |
| `domain` | `clause` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `gn` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `prs_gn` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `prs_ps` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `st` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `suffix_gender` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `suffix_person` | `word` | str | 4 | 1-8 | 0 | 0 | 0 | 0 |
| `nu` | `word` | str | 5 | 1-8 | 0 | 0 | 0 | 0 |
| `ps` | `word` | str | 5 | 1-8 | 0 | 0 | 0 | 0 |
| `qere_trailer` | `word` | str | 5 | 1-8 | 424698 | 566 | 0 | 2 |
| `qere_trailer_utf8` | `word` | str | 5 | 1-8 | 424698 | 566 | 0 | 2 |
| `rela` | `phrase_atom` | str | 6 | 1-8 | 0 | 0 | 0 | 0 |
| `uvf` | `word` | str | 6 | 1-8 | 0 | 0 | 0 | 0 |
| `rela` | `subphrase` | str | 7 | 1-8 | 0 | 0 | 0 | 0 |
| `number` | `phrase` | int | 9 | 9-32 | 0 | 0 | 0 | 0 |
| `vt` | `word` | str | 9 | 9-32 | 0 | 0 | 0 | 0 |
| `nametype` | `lex` | str | 10 | 9-32 | 6619 | 0 | 0 | 0 |
| `nametype` | `word` | str | 10 | 9-32 | 391084 | 0 | 0 | 0 |
| `pfm` | `word` | str | 11 | 9-32 | 0 | 11438 | 0 | 0 |
| `vbs` | `word` | str | 11 | 9-32 | 0 | 0 | 0 | 0 |
| `rela` | `clause` | str | 13 | 9-32 | 0 | 0 | 0 | 0 |
| `trailer` | `word` | str | 13 | 9-32 | 0 | 121801 | 0 | 11 |
| `trailer_utf8` | `word` | str | 13 | 9-32 | 0 | 121801 | 0 | 11 |
| `typ` | `phrase` | str | 13 | 9-32 | 0 | 0 | 0 | 0 |
| `typ` | `phrase_atom` | str | 13 | 9-32 | 0 | 0 | 0 | 0 |
| `ls` | `lex` | str | 14 | 9-32 | 8845 | 0 | 0 | 0 |
| `pdp` | `word` | str | 14 | 9-32 | 0 | 0 | 0 | 0 |
| `sp` | `lex` | str | 14 | 9-32 | 0 | 0 | 0 | 0 |
| `sp` | `word` | str | 14 | 9-32 | 0 | 0 | 0 | 0 |
| `ls` | `word` | str | 15 | 9-32 | 0 | 0 | 0 | 0 |
| `g_uvf_utf8` | `word` | str | 17 | 9-32 | 0 | 423048 | 0 | 0 |
| `g_uvf` | `word` | str | 19 | 9-32 | 0 | 423044 | 0 | 0 |
| `vbe` | `word` | str | 19 | 9-32 | 0 | 50655 | 0 | 0 |
| `dist` | `phrase_atom` | int | 20 | 9-32 | 0 | 0 | 0 | 0 |
| `nme` | `word` | str | 20 | 9-32 | 0 | 121983 | 0 | 0 |
| `prs` | `word` | str | 22 | 9-32 | 0 | 0 | 0 | 0 |
| `vs` | `word` | str | 26 | 9-32 | 0 | 0 | 0 | 0 |
| `dist` | `phrase` | int | 27 | 9-32 | 0 | 0 | 0 | 0 |
| `function` | `phrase` | str | 29 | 9-32 | 0 | 0 | 0 | 0 |
| `tab` | `clause_atom` | int | 30 | 9-32 | 0 | 0 | 0 | 0 |
| `dist` | `subphrase` | int | 31 | 9-32 | 0 | 0 | 0 | 0 |
| `number` | `clause` | int | 31 | 9-32 | 0 | 0 | 0 | 0 |
| `instruction` | `clause_atom` | str | 35 | 33-255 | 0 | 0 | 0 | 4 |
| `book@zh` | `book` | str | 38 | 33-255 | 0 | 0 | 0 | 0 |
| `book` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book` | `chapter` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book` | `verse` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@am` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@ar` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@bn` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@da` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@de` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@el` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@en` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@es` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@fa` | `book` | str | 39 | 33-255 | 0 | 0 | 2 | 0 |
| `book@fr` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@he` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@hi` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@id` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@ja` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@ko` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@la` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@nl` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@pa` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@pt` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@ru` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@sw` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@syc` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@tr` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@ur` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `book@yo` | `book` | str | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `dist` | `clause` | int | 39 | 33-255 | 0 | 0 | 0 | 0 |
| `typ` | `clause` | str | 42 | 33-255 | 0 | 0 | 0 | 0 |
| `typ` | `clause_atom` | str | 43 | 33-255 | 0 | 0 | 0 | 0 |
| `g_vbs_utf8` | `word` | str | 65 | 33-255 | 0 | 418195 | 18 | 0 |
| `g_vbs` | `word` | str | 66 | 33-255 | 0 | 411184 | 0 | 0 |
| `g_pfm_utf8` | `word` | str | 86 | 33-255 | 0 | 393045 | 30 | 0 |
| `g_pfm` | `word` | str | 87 | 33-255 | 0 | 381594 | 0 | 0 |
| `g_vbe_utf8` | `word` | str | 97 | 33-255 | 0 | 403547 | 12 | 2 |
| `g_vbe` | `word` | str | 101 | 33-255 | 0 | 352880 | 0 | 0 |
| `g_nme_utf8` | `word` | str | 106 | 33-255 | 0 | 245354 | 71 | 1 |
| `g_nme` | `word` | str | 108 | 33-255 | 0 | 245354 | 0 | 0 |
| `g_prs_utf8` | `word` | str | 126 | 33-255 | 0 | 383415 | 6 | 0 |
| `g_prs` | `word` | str | 127 | 33-255 | 0 | 381432 | 0 | 0 |
| `txt` | `clause` | str | 136 | 33-255 | 0 | 0 | 0 | 0 |
| `chapter` | `chapter` | int | 150 | 33-255 | 0 | 0 | 0 | 0 |
| `chapter` | `verse` | int | 150 | 33-255 | 0 | 0 | 0 | 0 |
| `dist` | `clause_atom` | int | 169 | 33-255 | 0 | 0 | 0 | 0 |
| `verse` | `verse` | int | 176 | 33-255 | 0 | 0 | 0 | 0 |
| `code` | `clause_atom` | int | 293 | 256-2000 | 0 | 0 | 0 | 0 |
| `number` | `sentence` | int | 338 | 256-2000 | 0 | 0 | 0 | 0 |
| `freq_occ` | `word` | int | 366 | 256-2000 | 0 | 0 | 0 | 0 |
| `rank_occ` | `word` | int | 367 | 256-2000 | 0 | 0 | 0 | 0 |
| `freq_lex` | `lex` | int | 372 | 256-2000 | 0 | 0 | 0 | 0 |
| `freq_lex` | `word` | int | 372 | 256-2000 | 0 | 0 | 0 | 0 |
| `lexeme_count` | `word` | int | 372 | 256-2000 | 0 | 0 | 0 | 0 |
| `rank_lex` | `lex` | int | 374 | 256-2000 | 0 | 0 | 0 | 0 |
| `rank_lex` | `word` | int | 374 | 256-2000 | 0 | 0 | 0 | 0 |
| `root` | `lex` | str | 757 | 256-2000 | 7818 | 0 | 0 | 0 |
| `root` | `word` | str | 757 | 256-2000 | 354539 | 0 | 0 | 0 |
| `qere_utf8` | `word` | str | 1261 | 256-2000 | 424698 | 25 | 638 | 0 |
| `qere` | `word` | str | 1262 | 256-2000 | 424698 | 25 | 0 | 0 |
| `kq_hybrid_utf8` | `word` | str | 1291 | 256-2000 | 0 | 424723 | 639 | 6 |
| `kq_hybrid` | `word` | str | 1294 | 256-2000 | 0 | 424698 | 0 | 0 |
| `pargr` | `clause_atom` | str | 3320 | >2000 | 0 | 0 | 0 | 0 |
| `number` | `sentence_atom` | int | 5188 | >2000 | 0 | 0 | 0 | 0 |
| `gloss` | `lex` | str | 6132 | >2000 | 0 | 0 | 0 | 986 |
| `gloss` | `word` | str | 6132 | >2000 | 0 | 0 | 0 | 986 |
| `lex0` | `lex` | str | 6461 | >2000 | 0 | 0 | 0 | 0 |
| `lex0` | `word` | str | 6461 | >2000 | 0 | 0 | 0 | 0 |
| `lex_utf8` | `word` | str | 6461 | >2000 | 0 | 0 | 0 | 219 |
| `lex_utf8` | `lex` | str | 7189 | >2000 | 0 | 0 | 0 | 219 |
| `number` | `clause_atom` | int | 7462 | >2000 | 0 | 0 | 0 | 0 |
| `voc_lex` | `lex` | str | 8091 | >2000 | 0 | 0 | 0 | 1 |
| `voc_lex` | `word` | str | 8091 | >2000 | 0 | 0 | 0 | 1 |
| `voc_lex_utf8` | `lex` | str | 8091 | >2000 | 0 | 0 | 3287 | 220 |
| `voc_lex_utf8` | `word` | str | 8091 | >2000 | 0 | 0 | 3287 | 220 |
| `lex` | `lex` | str | 8769 | >2000 | 0 | 0 | 0 | 0 |
| `lex` | `word` | str | 8769 | >2000 | 0 | 0 | 0 | 0 |
| `number` | `phrase_atom` | int | 18757 | >2000 | 0 | 0 | 0 | 0 |
| `g_lex_utf8` | `word` | str | 21134 | >2000 | 0 | 6488 | 9778 | 309 |
| `g_lex` | `word` | str | 21156 | >2000 | 0 | 11 | 0 | 0 |
| `label` | `verse` | str | 23213 | >2000 | 0 | 0 | 0 | 21054 |
| `g_cons` | `word` | str | 24439 | >2000 | 0 | 6488 | 0 | 0 |
| `g_cons_utf8` | `word` | str | 24439 | >2000 | 0 | 6488 | 0 | 265 |
| `number` | `word` | int | 29736 | >2000 | 0 | 0 | 0 | 0 |
| `g_word_utf8` | `word` | str | 92474 | >2000 | 0 | 6488 | 50369 | 305 |
| `g_word` | `word` | str | 92756 | >2000 | 0 | 0 | 0 | 0 |

## Bucket summary (feature, object type) pairs

| bucket | str | int |
|---|---:|---:|
| 1-8 | 31 | 0 |
| 9-32 | 22 | 6 |
| 33-255 | 43 | 5 |
| 256-2000 | 6 | 9 |
| >2000 | 20 | 4 |

## Edge features

| edge | values | (from type, to type): count |
|---|---|---|
| `distributional_parent` | False | word→phrase_atom: 426590; phrase_atom→clause_atom: 267532; clause_atom→sentence_atom: 90704 |
| `functional_parent` | False | word→phrase: 426590; phrase_atom→phrase: 267532; phrase→clause: 253203; clause_atom→clause: 90704; clause→sentence: 88131; sentence_atom→sentence: 64514 |
| `mother` | False | clause_atom→clause_atom: 89612; subphrase→word: 34989; subphrase→subphrase: 21936; clause→clause: 13917; phrase_atom→phrase_atom: 12498; clause→phrase: 5305; phrase_atom→word: 1831; clause→word: 1569; phrase→phrase: 552; phrase→clause: 52; phrase→word: 8 |
| `omap@2017-2021` | True | word→word: 426590; phrase_atom→phrase_atom: 267490; phrase→phrase: 253184; subphrase→subphrase: 184500; clause_atom→clause_atom: 90706; clause→clause: 88168; sentence_atom→sentence_atom: 64465; sentence→sentence: 63687; half_verse→half_verse: 45109; verse→verse: 23014; lex→lex: 9040; chapter→chapter: 923; sentence_atom→subphrase: 238; verse→lex: 200; subphrase→verse: 199; sentence→sentence_atom: 105; phrase_atom→sentence: 99; phrase→phrase_atom: 86; clause_atom→half_verse: 71; half_verse→phrase: 70; clause→clause_atom: 36; book→book: 33; word→book: 6; book→chapter: 6; chapter→clause: 6 |
| `omap@c-2021` | True | word→word: 426590; phrase_atom→phrase_atom: 267527; phrase→phrase: 253190; subphrase→subphrase: 184814; clause_atom→clause_atom: 90697; clause→clause: 88138; sentence_atom→sentence_atom: 64521; sentence→sentence: 63718; half_verse→half_verse: 45148; verse→verse: 23178; lex→lex: 9204; chapter→chapter: 923; verse→lex: 36; subphrase→verse: 35; book→book: 33; clause_atom→half_verse: 32; half_verse→phrase: 31; phrase→phrase_atom: 27; phrase_atom→sentence: 18; clause→clause_atom: 16; sentence→sentence_atom: 8; word→book: 6; book→chapter: 6; chapter→clause: 6; subphrase→sentence_atom: 3 |

## Hazards

- feature `book` has the same name as an object type
- feature `chapter` has the same name as an object type
- feature `lex` has the same name as an object type
- feature `verse` has the same name as an object type
