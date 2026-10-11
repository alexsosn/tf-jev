"""Model-free evidence runner for frozen, trusted BHSA benchmark gold.

Run from the checkout: python -m scripts.nl_benchmark_v2 CORPUS_DIRECTORY
Held-out data is evaluation-only; never import it into parser prompt construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from tests.conformance.tf_harness import run_template

DEFAULT = Path(__file__).resolve().parents[1] / "benchmarks/nl-tf-v2/bhsa-2021.json"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
FEATURE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
PARTITIONS = {"development", "heldout"}


class BenchmarkError(ValueError):
    """Invalid artifact, corpus mismatch or failed native search."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def fields(value: Any, required: set[str], optional: set[str] | None = None) -> None:
    require(isinstance(value, dict), "expected an object")
    require(required <= value.keys() <= required | (optional or set()), "unexpected/missing fields")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def projection_valid(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and bool(value)
        and all(type(i) is int and i >= 0 for i in value)
        and len(set(value)) == len(value)
    )


def projected(
    rows: Iterable[tuple[int, ...]], projection: tuple[int, ...]
) -> list[tuple[int, ...]]:
    require(projection_valid(projection), "invalid projection")
    values: set[tuple[int, ...]] = set()
    for row in rows:
        require(all(type(n) is int and n > 0 for n in row), "invalid node IDs")
        require(max(projection) < len(row), "projection column missing")
        values.add(tuple(row[i] for i in projection))
    return sorted(values)


def signature(rows: Iterable[tuple[int, ...]], projection: tuple[int, ...]) -> str:
    payload = {"width": len(projection), "rows": projected(rows, projection)}
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Benchmark:
    corpus: dict[str, str]
    features: tuple[str, ...]
    source_sha256: dict[str, str]
    cases: tuple[dict[str, Any], ...]

    def selected(self, partition: str = "development") -> tuple[dict[str, Any], ...]:
        require(isinstance(partition, str) and partition in PARTITIONS, "invalid partition")
        return tuple(c for c in self.cases if c["partition"] == partition)

    def verify_source(self, directory: Path) -> None:
        require(
            version("text-fabric") == self.corpus["text_fabric"], "Text-Fabric version mismatch"
        )
        for filename, digest in self.source_sha256.items():
            try:
                actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
            except OSError as error:
                raise BenchmarkError(f"source unavailable: {filename}") from error
            require(actual == digest, f"source mismatch: {filename}")


def load_benchmark(path: Path = DEFAULT) -> Benchmark:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BenchmarkError("cannot read benchmark JSON") from error
    fields(data, {"version", "corpus", "features", "source_sha256", "cases"})
    require(data["version"] == "nl-tf-v2", "unsupported benchmark version")
    corpus = data["corpus"]
    fields(corpus, {"name", "version", "text_fabric"})
    require(
        corpus == {"name": "BHSA", "version": "2021", "text_fabric": "13.1.0"},
        "unsupported corpus contract",
    )
    features = data["features"]
    require(isinstance(features, list) and bool(features), "missing features")
    require(
        all(isinstance(f, str) and FEATURE.fullmatch(f) for f in features), "invalid feature name"
    )
    require(len(set(features)) == len(features), "duplicate feature")
    hashes = data["source_sha256"]
    require(isinstance(hashes, dict), "missing source hashes")
    require(
        set(hashes) == {f + ".tf" for f in (*features, "otype", "oslots", "otext")},
        "source coverage mismatch",
    )
    require(
        all(isinstance(h, str) and DIGEST.fullmatch(h) for h in hashes.values()),
        "invalid source digest",
    )
    cases = data["cases"]
    require(isinstance(cases, list) and bool(cases), "missing cases")
    ids: set[str] = set()
    requests: set[str] = set()
    families: dict[str, str] = {}
    for case in cases:
        fields(
            case,
            {"id", "family", "partition", "request", "expected", "rationale"},
            {"gold", "interpretations"},
        )
        require(
            all(
                nonempty(case[k])
                for k in ("id", "family", "request", "rationale", "partition", "expected")
            ),
            "empty case field",
        )
        require(case["id"] not in ids and case["request"] not in requests, "duplicate case")
        ids.add(case["id"])
        requests.add(case["request"])
        require(case["partition"] in PARTITIONS, "invalid case partition")
        require(
            families.get(case["family"], case["partition"]) == case["partition"],
            "family crosses partitions",
        )
        families[case["family"]] = case["partition"]
        require(
            case["expected"] in {"supported", "ambiguous", "unsupported"}, "invalid expected class"
        )
        if case["expected"] == "supported":
            require(
                "gold" in case and "interpretations" not in case,
                "supported case requires only gold",
            )
            gold = case["gold"]
            fields(gold, {"query", "projection", "count", "signature"})
            require(
                nonempty(gold["query"]) and projection_valid(gold["projection"]),
                "invalid gold query/projection",
            )
            require(type(gold["count"]) is int and gold["count"] >= 0, "invalid gold count")
            require(
                isinstance(gold["signature"], str)
                and DIGEST.fullmatch(gold["signature"]) is not None,
                "invalid gold signature",
            )
        else:
            require("gold" not in case, "abstention must not have gold")
            if case["expected"] == "ambiguous":
                alternatives = case.get("interpretations")
                require(isinstance(alternatives, list), "missing interpretations")
                require(
                    len(alternatives) >= 2 and all(nonempty(a) for a in alternatives),
                    "invalid interpretations",
                )
                require(len(set(alternatives)) == len(alternatives), "duplicate interpretations")
            else:
                require(
                    "interpretations" not in case, "unsupported case must state reason in rationale"
                )
    return Benchmark(corpus, tuple(features), hashes, tuple(cases))


def execute(
    api: Any, query: str, projection: tuple[int, ...], *, limit: int = 500_000
) -> tuple[int, str]:
    require(type(limit) is int and limit > 0, "invalid result limit")
    outcome = run_template(api, query, limit=limit)
    require(outcome.ok and outcome.results is not None, "native TF reported errors or overflow")
    assert outcome.results is not None
    rows = outcome.results
    require(projection_valid(projection), "invalid projection")
    require(
        outcome.arity is not None and max(projection) < outcome.arity, "projection column missing"
    )
    # A limit may return a complete-looking prefix without an overflow diagnostic.
    # Reject reaching the cap conservatively, even if the full query had exactly that count.
    require(len(rows) < limit, "native result limit reached")
    values = projected(rows, projection)
    return len(values), signature(values, tuple(range(len(projection))))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_directory", type=Path)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT)
    parser.add_argument("--partition", choices=sorted(PARTITIONS), default="development")
    args = parser.parse_args()
    try:
        benchmark = load_benchmark(args.benchmark)
        benchmark.verify_source(args.corpus_directory)
        api = Fabric(locations=str(args.corpus_directory), silent="deep").load(
            " ".join(benchmark.features), silent="deep"
        )
        require(bool(api), "cannot load corpus")
        counts: Counter[str] = Counter()
        for case in benchmark.selected(args.partition):
            counts[case["expected"]] += 1
            if case["expected"] == "supported":
                gold = case["gold"]
                result = execute(api, gold["query"], tuple(gold["projection"]))
                require(
                    result == (gold["count"], gold["signature"]), f"gold mismatch: {case['id']}"
                )
        print(
            json.dumps(
                {
                    "version": "nl-tf-v2",
                    "partition": args.partition,
                    "classes": dict(counts),
                    "gold_verified": counts["supported"],
                },
                sort_keys=True,
            )
        )
    except BenchmarkError as error:
        parser.exit(1, f"benchmark failed: {error}\n")


if __name__ == "__main__":
    main()
