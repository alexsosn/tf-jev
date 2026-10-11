"""One-session, pinned BHSA 2021 native replay for benchmark research (#10).

No Text-Fabric search is synthesized from NL. Both catalogues are trusted
version-controlled fixtures. This command has no network/model interaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from scripts.bhsa_gold_ir import validate_promotions
from scripts.nl_benchmark import check_gold, load_catalog, verify_source
from scripts.nl_candidates import (
    UPSTREAM_COMMIT,
    load_candidates,
    run_candidate,
    verify_candidate_source,
)
from tests.conformance.tf_harness import load_api

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "benchmarks/nl-tf-v1/bhsa-2021.json"
CANDIDATES = ROOT / "benchmarks/nl-tf-v1/tutorial-candidates.json"

# Includes every feature explicitly referenced by either gold or in-scope queries.
# All source files loaded by Text-Fabric are authenticated via the pinned Git tree
# when the companion GitHub Actions workflow checks out the immutable corpus commit.
FEATURES = "sp gn nu lex prs function typ verse book vs vt ps qere dist rela mother"


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def replay(
    corpus: Path, gold_path: Path = GOLD, candidate_path: Path = CANDIDATES
) -> dict[str, Any]:
    """Verify the source first, then replay all gold and in-scope candidates.

    Raises rather than returning an incomplete or purportedly passing report
    when *any* referenced source, gold count or native query fails.
    """
    gold = load_catalog(gold_path)
    candidates = load_candidates(candidate_path)
    if (
        corpus.name != "2021"
        or gold.corpus != candidates.corpus
        or gold.data_version != candidates.target_data_version
    ):
        raise ValueError("BHSA corpus version mismatch")
    verify_source(corpus, gold)
    verify_candidate_source(corpus, candidates)

    api = load_api(corpus, features=FEATURES)
    if not api:
        raise ValueError("native BHSA Text-Fabric API could not be loaded")

    confirmed = 0
    for case in gold.cases:
        if case.status == "supported":
            check_gold(api, case)
            confirmed += 1
    validate_promotions(api, gold)

    observations: list[dict[str, Any]] = []
    for candidate in candidates.cases:
        if candidate.capability != "in_scope":
            continue
        observed = run_candidate(api, candidate)
        source_version = candidates.notebooks[candidate.source_file].data_version
        observations.append(
            {
                "id": candidate.id,
                "notebook_data_version": source_version,
                "observed_2021_rows": observed,
                "historical_notebook_rows": candidate.reported_count,
                "agrees_with_notebook": observed == candidate.reported_count,
            }
        )

    return {
        "format_version": 1,
        "purpose": "native-replay-not-gold-promotion",
        "corpus": gold.corpus,
        "data_version": gold.data_version,
        "source_commit": UPSTREAM_COMMIT,
        "gold_fixture_sha256": _sha256(gold_path),
        "candidate_fixture_sha256": _sha256(candidate_path),
        "gold_checked": confirmed,
        "candidate_checked": len(observations),
        "observations": observations,
    }


def write_report(
    output: Path, report: dict[str, Any], *, protected_paths: tuple[Path, ...] = (GOLD, CANDIDATES)
) -> None:
    """Write the complete result atomically; never overwrite either input fixture."""
    if output.resolve() in {path.resolve() for path in protected_paths}:
        raise ValueError("refusing to overwrite a source fixture")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, prefix=".bhsa-replay-", delete=False
        ) as file:
            tmp = Path(file.name)
            json.dump(report, file, sort_keys=True, indent=2)
            file.write("\n")
        os.replace(tmp, output)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)



def verify_reference_report(report: dict[str, Any], reference_path: Path) -> None:
    """Refuse corpus/fixture/count drift against reviewed native observations.

    Canonical serialized JSON comparison deliberately distinguishes bool from int,
    unlike Python dict equality. This fixture records native behavior, not NL gold.
    """
    try:
        expected = json.loads(reference_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("native reference unavailable or malformed") from error
    def canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if canonical(report) != canonical(expected):
        raise ValueError("native reference mismatch (counts, source or fixture identity)")



def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recheck verified BHSA 2021 native gold and tutorial candidates"
    )
    parser.add_argument(
        "--corpus", required=True, type=Path, help="local ETCBC/bhsa/tf/2021 directory"
    )
    parser.add_argument("--gold", type=Path, default=GOLD)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES)
    parser.add_argument(
        "--expected", type=Path, help="optional frozen native-only observation reference"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="new JSON summary (no corpus text)"
    )
    args = parser.parse_args()
    try:
        # Fail before expensive loading if caller points --output at a pinned fixture.
        protected = (args.gold, args.candidates, *([args.expected] if args.expected else []))
        if args.output.resolve() in {path.resolve() for path in protected}:
            raise ValueError("refusing to overwrite a source fixture")
        report = replay(args.corpus, args.gold, args.candidates)
        if args.expected is not None:
            verify_reference_report(report, args.expected)
        write_report(args.output, report, protected_paths=protected)
        print(json.dumps(report, sort_keys=True))
    except (ValueError, OSError) as error:
        parser.exit(1, f"BHSA 2021 replay failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
