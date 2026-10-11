"""Frozen real-domain benchmark; gold comes from loaded TF, not the retrieval index."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from tf_jev.retrieval import Match, Normalization, RetrievalError, RetrievalIndex
from tf_jev.schema import Large, extract_schema


def test_bhsa_retrieval_benchmark(bhsa_api: Any, bhsa_dir: Path) -> None:
    benchmark = json.loads(
        (Path(__file__).parents[1] / "benchmarks/retrieval-v1/bhsa-2021.json").read_text()
    )
    for filename, digest in benchmark["source_sha256"].items():
        assert hashlib.sha256((bhsa_dir / filename).read_bytes()).hexdigest() == digest
    schema = extract_schema(bhsa_api)
    raw = {
        feature: Counter(
            v for n, v in bhsa_api.Fs(feature).items() if bhsa_api.F.otype.v(n) == "word"
        )
        for feature in ("lex", "voc_lex_utf8", "gloss")
    }
    indexes = {}
    metrics: Counter[str] = Counter()
    for case in benchmark["cases"]:
        feature, mode = case["feature"], Normalization(case["normalization"])
        if (feature, mode) not in indexes:
            kind = schema.domain(feature, "word").kind
            assert isinstance(kind, Large)
            indexes[feature, mode] = RetrievalIndex.from_schema(
                schema, kind.retrieval_handle, normalization=mode
            )
        result = indexes[feature, mode].lookup(case["text"], match=Match(case["match"]))

        # Independent linear raw-domain oracle; never calls production key/index helpers.
        def key(value: str, normalization: str = case["normalization"]) -> str:
            if normalization == "exact":
                return value
            normalized = unicodedata.normalize("NFC", value)
            if normalization == "nfc_casefold":
                return unicodedata.normalize("NFC", normalized.casefold())
            return normalized

        matches = sorted(
            (
                v
                for v in raw[feature]
                if (
                    key(v) == key(case["text"])
                    if case["match"] == "exact"
                    else key(v).startswith(key(case["text"]))
                )
            ),
            key=lambda v: (key(v), v),
        )
        assert result.total_matches == len(matches)
        assert [c.value for c in result.candidates] == matches[:32]
        assert all(c.count == raw[feature][c.value] for c in result.candidates)
        assert set(case["gold"]) <= set(matches)
        metrics["cases"] += 1
        metrics["gold_values"] += len(case["gold"])
        metrics["gold_included"] += len(set(case["gold"]) & {c.value for c in result.candidates})
        metrics["no_match"] += not matches
        metrics["overflow"] += result.truncated
        if matches and not result.truncated:
            question = result.as_question("Select an attested value")
            assert len(question.options) <= 32
            metrics["handoff_eligible"] += 1
            metrics["eligible_gold"] += len(case["gold"])
            metrics["eligible_gold_included"] += len(case["gold"])
        else:
            try:
                result.as_question("Select an attested value")
            except RetrievalError:
                pass
            else:
                raise AssertionError("unsafe handoff")
    print("\nretrieval-v1 metrics:", json.dumps(dict(sorted(metrics.items())), sort_keys=True))
    assert metrics["eligible_gold"] == metrics["eligible_gold_included"]
    assert metrics["overflow"] == 2 and metrics["no_match"] == 3
