"""Strict intake and opt-in replay of official BHSA tutorial queries.

These are *discovery candidates*, never held-out or verified 2021 gold queries.
No NL parsing, model calls, downloads, or automatic promotion occur here.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from scripts.nl_benchmark import MAX_ROWS, _git_blob_sha
from tests.conformance.tf_harness import load_api, run_template

KNOWN_NOTEBOOKS = frozenset(
    {
        "search.ipynb",
        "searchAdvanced.ipynb",
        "searchRelations.ipynb",
        "searchFromMQL.ipynb",
        "searchQuantifiers.ipynb",
    }
)
UPSTREAM_COMMIT = "4db00e2157915495e1a4d3d57e41223df24775da"
GIT_FILES = frozenset(
    {
        "otype.tf",
        "oslots.tf",
        "sp.tf",
        "gn.tf",
        "nu.tf",
        "book.tf",
        "vs.tf",
        "vt.tf",
        "ps.tf",
        "qere.tf",
        "dist.tf",
        "typ.tf",
        "lex.tf",
        "rela.tf",
        "function.tf",
        "g_cons.tf",
    }
)
ROOT_FIELDS = frozenset(
    {
        "format_version",
        "purpose",
        "corpus",
        "target_data_version",
        "upstream_commit",
        "notebooks",
        "source_git_blobs",
        "cases",
    }
)
NOTEBOOK_FIELDS = frozenset({"blob_sha", "data_version"})
CASE_FIELDS = frozenset(
    {
        "id",
        "source_file",
        "source_cell",
        "capability",
        "query",
        "request",
        "reported_count",
        "rationale",
    }
)


@dataclass(frozen=True)
class Notebook:
    blob_sha: str
    data_version: str


@dataclass(frozen=True)
class Candidate:
    id: str
    source_file: str
    source_cell: int
    capability: str
    query: str
    request: str
    reported_count: int | None
    rationale: str


@dataclass(frozen=True)
class CandidateCatalog:
    corpus: str
    target_data_version: str
    notebooks: Mapping[str, Notebook]
    source_git_blobs: tuple[tuple[str, str], ...]
    cases: tuple[Candidate, ...]


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key in tutorial candidate JSON")
        result[key] = value
    return result


def _fields(value: Any, required: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != required:
        raise ValueError("unexpected tutorial candidate fields")
    return value


def _text(value: Any) -> str:
    if type(value) is not str or not value.strip() or "\x00" in value:
        raise ValueError("invalid tutorial candidate text")
    return value


def _sha(value: Any, size: int) -> str:
    if type(value) is not str or re.fullmatch(f"[0-9a-f]{{{size}}}", value) is None:
        raise ValueError("invalid tutorial source SHA")
    return value


def load_candidates(path: Path) -> CandidateCatalog:
    """Strictly validate provenance and keep old notebook counts separate from gold."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("tutorial candidate fixture unavailable or malformed") from error
    root = _fields(raw, ROOT_FIELDS)
    if (
        type(root["format_version"]) is not int
        or root["format_version"] != 1
        or root["purpose"] != "discovery-only"
        or root["corpus"] != "ETCBC/bhsa"
        or root["target_data_version"] != "2021"
        or root["upstream_commit"] != UPSTREAM_COMMIT
    ):
        raise ValueError("unexpected corpus/version/discovery purpose")
    entries = _fields(root["notebooks"], KNOWN_NOTEBOOKS)
    notebooks: dict[str, Notebook] = {}
    for name, metadata in entries.items():
        record = _fields(metadata, NOTEBOOK_FIELDS)
        ver = _text(record["data_version"])
        if ver != ("2017" if name == "searchFromMQL.ipynb" else "unversioned"):
            raise ValueError("source notebook data-version mismatch")
        notebooks[name] = Notebook(_sha(record["blob_sha"], 40), ver)
    sources = _fields(root["source_git_blobs"], GIT_FILES)
    source_git_blobs = tuple(
        sorted((name, _sha(sha, 40)) for name, sha in sources.items())
    )
    records = root["cases"]
    if type(records) is not list or not records:
        raise ValueError("empty or invalid tutorial candidate cases")
    cases: list[Candidate] = []
    ids: set[str] = set()
    for raw_case in records:
        case = _fields(raw_case, CASE_FIELDS)
        identifier = _text(case["id"])
        if re.fullmatch("[a-z0-9][a-z0-9-]*", identifier) is None or identifier in ids:
            raise ValueError("duplicate or malformed tutorial candidate ID")
        ids.add(identifier)
        filename = _text(case["source_file"])
        if filename not in notebooks:
            raise ValueError("candidate has unknown source notebook")
        cell = case["source_cell"]
        if type(cell) is not int or cell < 0:
            raise ValueError("candidate source cell must be a nonnegative integer")
        capability = _text(case["capability"])
        if capability not in ("in_scope", "deferred"):
            raise ValueError("unknown tutorial candidate capability")
        reported = case["reported_count"]
        if reported is not None and (type(reported) is not int or reported < 0):
            raise ValueError("invalid unverified historical result count")
        cases.append(
            Candidate(
                identifier,
                filename,
                cell,
                capability,
                _text(case["query"]),
                _text(case["request"]),
                reported,
                _text(case["rationale"]),
            )
        )
    return CandidateCatalog(
        root["corpus"],
        root["target_data_version"],
        MappingProxyType(notebooks),
        source_git_blobs,
        tuple(cases),
    )


def verify_candidate_source(directory: Path, catalog: CandidateCatalog) -> None:
    """Refuse to execute on raw corpus files that diverge from BHSA 2021."""
    if directory.name != catalog.target_data_version:
        raise ValueError("candidate corpus directory must be tf/2021")
    try:
        for name, expected in catalog.source_git_blobs:
            if _git_blob_sha(directory / name) != expected:
                raise ValueError("candidate corpus source digest mismatch")
    except OSError as error:
        raise ValueError("candidate corpus source is unavailable") from error


def run_candidate(api: Any, case: Candidate, *, max_rows: int = MAX_ROWS) -> int:
    """Report *observed* native cardinality; never trust a notebook's old count."""
    if case.capability != "in_scope":
        raise ValueError("deferred tutorial construct cannot enter the prototype benchmark")
    if type(max_rows) is not int or not 0 < max_rows <= MAX_ROWS:
        raise ValueError("invalid native replay row limit")
    outcome = run_template(api, case.query, limit=max_rows + 1)
    if not outcome.ok or outcome.results is None:
        raise ValueError(f"invalid native tutorial candidate: {case.id}")
    if len(outcome.results) > max_rows:
        raise ValueError(f"native tutorial candidate row limit exceeded: {case.id}")
    return len(outcome.results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and optionally replay tutorial examples")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "benchmarks/nl-tf-v1/tutorial-candidates.json",
    )
    parser.add_argument("--corpus", type=Path, help="opt-in local BHSA tf/2021 directory")
    args = parser.parse_args()
    try:
        catalog = load_candidates(args.dataset)
        report: dict[str, Any] = {
            "purpose": "discovery-only",
            "cases": len(catalog.cases),
            "in_scope": sum(c.capability == "in_scope" for c in catalog.cases),
            "deferred": sum(c.capability == "deferred" for c in catalog.cases),
            "native_checked": 0,
        }
        if args.corpus is not None:
            verify_candidate_source(args.corpus, catalog)
            api = load_api(
                args.corpus,
                features="sp gn nu book vs vt ps qere dist typ lex rela function",
            )
            results: list[dict[str, Any]] = []
            for case in catalog.cases:
                if case.capability != "in_scope":
                    continue
                observed = run_candidate(api, case)
                results.append(
                    {
                        "id": case.id,
                        "observed_2021_rows": observed,
                        "historical_notebook_rows": case.reported_count,
                        "notebook_data_version": catalog.notebooks[case.source_file].data_version,
                        "agrees_with_notebook": observed == case.reported_count,
                    }
                )
            report["native_checked"] = len(results)
            report["observations"] = results
        print(json.dumps(report, sort_keys=True))
    except ValueError as error:
        parser.exit(1, f"tutorial candidate validation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
