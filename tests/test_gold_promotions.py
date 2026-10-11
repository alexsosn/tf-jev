"""RED-first adjudication tests for six official BHSA 2021 semantic gold cases (#10)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.bhsa_gold_ir import PROMOTED_IR, validate_promotions
from scripts.nl_benchmark import PINNED_FILES, equivalent, load_catalog, verify_source
from tests.test_compiler import NativeSymbols
from tf_jev.compiler import compile_query

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "benchmarks/nl-tf-v1/bhsa-2021.json"
PROMOTIONS = {
    "words-all": ("train", 426590),
    "feminine-plural-substantives": ("development", 5992),
    "qere-present": ("train", 1892),
    "qere-missing": ("development", 424698),
    "samuel-proper-noun-context": ("train", 1868),
    "same-slots-verse-sentence": ("development", 3583),
    "clauses-distance-one": ("train", 598),
    "clauses-distance-less-minus-ten": ("development", 86),
    "clause-adjacent-phrases": ("development", 162653),
    "sentence-clause-phrase-order": ("train", 136137),
    "pp-prep-adj-noun": ("development", 61),
}


def test_promotions_are_typed_and_unsealed() -> None:
    catalog = load_catalog(GOLD)
    indexed = {c.id: c for c in catalog.cases}
    assert len(catalog.cases) == 24
    assert set(PROMOTED_IR) == set(PROMOTIONS)
    assert len({c.id for c in catalog.cases}) == len(catalog.cases)
    assert all(
        indexed[case_id].split == split
        and indexed[case_id].expected_count == expected
        and indexed[case_id].status == "supported"
        and indexed[case_id].gold_query
        for case_id, (split, expected) in PROMOTIONS.items()
    )
    assert all(indexed[x].split != "evaluation" for x in PROMOTED_IR)
    assert {"book.tf", "qere.tf", "dist.tf", "typ.tf"} <= PINNED_FILES
    assert {"book.tf", "qere.tf", "dist.tf", "typ.tf"} <= dict(catalog.source_git_blobs).keys()
    assert len([c for c in catalog.cases if c.split == "evaluation"]) == 5


def test_compilation_of_simple_adjudicated_ir_on_real_tiny_tf(tiny_api: Any) -> None:
    schema = NativeSymbols(tiny_api)
    word_query = compile_query(PROMOTED_IR["words-all"], schema)
    feminine_query = compile_query(PROMOTED_IR["feminine-plural-substantives"], schema)
    assert equivalent(tiny_api, "word", word_query, max_rows=20)
    assert equivalent(tiny_api, "word gn=f nu=pl sp=subs", feminine_query, max_rows=20)
    # Same-slots relation still requires both SAME_SLOTS and nesting.
    assert len(PROMOTED_IR["same-slots-verse-sentence"].relations) == 2


def test_all_promoted_ir_match_full_native_bhsa_result_tuples(
    bhsa_api: Any, bhsa_dir: Path
) -> None:
    bhsa_api.TF.load("book qere", add=True, silent="deep")
    catalog = load_catalog(GOLD)
    verify_source(bhsa_dir, catalog)
    assert validate_promotions(bhsa_api, catalog) == len(PROMOTIONS)


def test_no_hardcoded_native_search_fragments_inside_ir_values() -> None:
    for witness in PROMOTED_IR.values():
        assert all("\\n" not in atom.object_type for atom in witness.atoms)
        assert all(
            all("\\n" not in str(v) for v in predicate.values)
            for atom in witness.atoms
            for predicate in atom.predicates
        )


def test_guard_rejects_mismatched_semantic_gold(
    tiny_api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No accidental execution against a fixture whose six gold cases are absent.
    from dataclasses import replace

    catalog = load_catalog(GOLD)
    wrong = replace(catalog, cases=tuple(c for c in catalog.cases if c.id != "words-all"))
    with pytest.raises(ValueError, match="promoted"):
        validate_promotions(tiny_api, wrong)


def test_new_typed_relations_and_signed_distance_are_expressed_without_native_strings() -> None:
    """Real-data replay must independently confirm these planned IR witnesses."""
    from tf_jev.ir import PredicateOp, RelationOp

    lower = PROMOTED_IR["clauses-distance-less-minus-ten"]
    assert lower.atoms[0].predicates[0].feature == "dist"
    assert lower.atoms[0].predicates[0].operator is PredicateOp.LT
    assert lower.atoms[0].predicates[0].values == (-10,)

    consecutive = PROMOTED_IR["clause-adjacent-phrases"]
    assert len(consecutive.atoms) == 3
    assert sum(rel.operator is RelationOp.ADJACENT_BEFORE for rel in consecutive.relations) == 1
    assert sum(rel.operator is RelationOp.EMBEDS for rel in consecutive.relations) == 2

    pp = PROMOTED_IR["pp-prep-adj-noun"]
    assert len(pp.atoms) == 4
    assert sum(rel.operator is RelationOp.ADJACENT_BEFORE for rel in pp.relations) == 2
    assert sum(rel.operator is RelationOp.EMBEDS for rel in pp.relations) == 3

    ordering = PROMOTED_IR["sentence-clause-phrase-order"]
    assert len(ordering.atoms) == 4
    assert sum(rel.operator is RelationOp.BEFORE for rel in ordering.relations) == 1
    assert sum(rel.operator is RelationOp.AFTER for rel in ordering.relations) == 1
