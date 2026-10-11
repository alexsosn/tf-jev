"""Versioned NL → native-Text-Fabric benchmark validation tooling.

Research-only harness; never interprets request prose or calls model backends.
Candidate queries passed to `equivalent` must be compiler-produced/trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tests.conformance.tf_harness import load_api, run_template

SPLITS = frozenset({"train", "development", "evaluation"})
STATUSES = frozenset({"supported", "ambiguous", "unsupported"})
MAX_ROWS = 500_000
PINNED_FILES = frozenset(
    {"otype.tf", "oslots.tf", "sp.tf", "gn.tf", "nu.tf", "function.tf",
     "mother.tf", "book.tf", "qere.tf", "dist.tf", "typ.tf",
     "vs.tf", "vt.tf", "ps.tf", "lex.tf", "rela.tf"}
)
ROOT_FIELDS = frozenset(
    {"format_version", "corpus", "data_version", "source_sha256", "source_git_blobs", "cases"}
)
CASE_FIELDS = frozenset(
    {
        "id",
        "split",
        "status",
        "difficulty",
        "request",
        "gold_query",
        "expected_count",
        "rationale",
    }
)


@dataclass(frozen=True)
class Case:
    id: str
    split: str
    status: str
    difficulty: str
    request: str
    gold_query: str | None
    expected_count: int | None
    rationale: str


@dataclass(frozen=True)
class Catalog:
    corpus: str
    data_version: str
    source_sha256: str
    source_git_blobs: tuple[tuple[str, str], ...]
    cases: tuple[Case, ...]


def _fields(value: Any, expected: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise ValueError("benchmark record has missing or unknown fields")
    return value


def _text(value: Any) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError("benchmark requires nonempty text")
    return value


def load_catalog(path: Path) -> Catalog:
    """Parse a strictly typed, frozen benchmark fixture without executing queries."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("benchmark JSON is unavailable or malformed") from error
    root = _fields(raw, ROOT_FIELDS)
    if type(root["format_version"]) is not int or root["format_version"] != 1:
        raise ValueError("unsupported benchmark format version")
    if _text(root["corpus"]) != "ETCBC/bhsa" or _text(root["data_version"]) != "2021":
        raise ValueError("unsupported pinned corpus/version")
    source = _fields(root["source_sha256"], frozenset({"otype.tf"}))["otype.tf"]
    if type(source) is not str or re.fullmatch(r"[0-9a-f]{64}", source) is None:
        raise ValueError("invalid source digest")
    raw_blobs = _fields(root["source_git_blobs"], PINNED_FILES)
    blobs: list[tuple[str, str]] = []
    for name, digest in sorted(raw_blobs.items()):
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{40}", digest) is None:
            raise ValueError("invalid Git source digest")
        blobs.append((name, digest))
    records = root["cases"]
    if type(records) is not list or not records:
        raise ValueError("benchmark cases must be a nonempty list")
    cases: list[Case] = []
    ids: set[str] = set()
    for record in records:
        row = _fields(record, CASE_FIELDS)
        identifier = _text(row["id"])
        if identifier in ids or re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier) is None:
            raise ValueError("duplicate or invalid benchmark case id")
        ids.add(identifier)
        split = _text(row["split"])
        status = _text(row["status"])
        if split not in SPLITS or status not in STATUSES:
            raise ValueError("unknown benchmark split/status")
        difficulty = _text(row["difficulty"])
        request = _text(row["request"])
        rationale = _text(row["rationale"])
        gold = row["gold_query"]
        count = row["expected_count"]
        if status == "supported":
            gold = _text(gold)
            if type(count) is not int or not 0 <= count < MAX_ROWS:
                raise ValueError("supported query requires a bounded exact count")
        elif gold is not None or count is not None:
            raise ValueError("abstention cases must not have gold native queries or counts")
        cases.append(Case(identifier, split, status, difficulty, request, gold, count, rationale))
    return Catalog(root["corpus"], root["data_version"], source, tuple(blobs), tuple(cases))


def _git_blob_sha(path: Path) -> str:
    """Verify the content SHA from the upstream Git tree without loading it into memory."""
    digest = hashlib.sha1()
    digest.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(directory: Path, catalog: Catalog) -> None:
    """Fail closed if any referenced BHSA feature or structural source differs."""
    try:
        with (directory / "otype.tf").open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != catalog.source_sha256:
            raise ValueError("benchmark corpus source digest mismatch")
        for name, expected in catalog.source_git_blobs:
            if _git_blob_sha(directory / name) != expected:
                raise ValueError("benchmark corpus source Git digest mismatch")
    except OSError as error:
        raise ValueError("benchmark corpus source is unavailable") from error

def check_gold(api: Any, case: Case) -> int:
    """Validate a supported native gold query and its exact, untruncated row count."""
    if case.status != "supported" or case.gold_query is None or case.expected_count is None:
        raise ValueError("only supported cases have native gold queries")
    count = case.expected_count
    if type(count) is not int or not 0 <= count < MAX_ROWS:
        raise ValueError("invalid gold row count")
    # An explicit TF limit truncates silently. Request one more than gold count.
    result = run_template(api, case.gold_query, limit=count + 1)
    if not result.ok or result.results is None:
        raise ValueError(f"invalid native gold query: {case.id}")
    actual = len(result.results)
    if actual != count:
        raise ValueError(f"native gold count mismatch: {case.id}: expected {count}, got {actual}")
    return actual


def equivalent(api: Any, gold: str, candidate: str, *, max_rows: int = MAX_ROWS) -> bool:
    """Compare full native tuples, not counts. Accept trusted compiled candidate queries only."""
    if type(max_rows) is not int or not 0 < max_rows <= MAX_ROWS:
        raise ValueError("invalid comparison row limit")
    outcomes = []
    for template in (gold, candidate):
        result = run_template(api, template, limit=max_rows + 1)
        if not result.ok or result.results is None:
            raise ValueError("invalid native query in equivalence check")
        if len(result.results) > max_rows:
            raise ValueError("native equivalence row limit exceeded")
        outcomes.append(result.results)
    return outcomes[0] == outcomes[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pinned NL ↔ TF gold cases")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "benchmarks/nl-tf-v1/bhsa-2021.json",
    )
    parser.add_argument("--corpus", type=Path, help="local pinned BHSA tf/2021 directory")
    args = parser.parse_args()
    try:
        catalog = load_catalog(args.dataset)
        counts = {
            status: sum(c.status == status for c in catalog.cases) for status in sorted(STATUSES)
        }
        report: dict[str, Any] = {
            "cases": len(catalog.cases),
            "status": counts,
            "native_checked": 0,
        }
        if args.corpus is not None:
            if args.corpus.name != catalog.data_version:
                raise ValueError("benchmark corpus directory must be named after data version")
            verify_source(args.corpus, catalog)
            api = load_api(
                args.corpus,
                features="sp gn nu lex prs function typ verse book qere dist mother",
            )
            report["native_checked"] = len(
                [check_gold(api, case) for case in catalog.cases if case.status == "supported"]
            )
        print(json.dumps(report, sort_keys=True))
    except ValueError as error:
        parser.exit(1, f"benchmark validation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
