"""Introspect a Text-Fabric dataset's query-relevant schema (research probe for #4).

Generic: no corpus-specific feature names. Prints a Markdown report with object
types, node/edge features, per-(feature, object type) value cardinalities and
hazards for query compilation.

    python scripts/probe_corpus_schema.py ~/text-fabric-data/github/ETCBC/bhsa/tf/2021

This is evidence tooling, not production API; the CorpusSchema contract is
proposed in docs/research/corpus-schema.md.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import re
import sys
import time
import unicodedata
from importlib.metadata import version
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

# Bounded-choice buckets, see docs/research/corpus-schema.md §4.
BUCKETS = ((8, "1-8"), (32, "9-32"), (255, "33-255"), (2000, "256-2000"))
SAFE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_@-]*")
ESCAPED = (" ", "|", "\\")


def bucket(k: int) -> str:
    for limit, name in BUCKETS:
        if k <= limit:
            return name
    return ">2000"


def content_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.glob("*.tf") if p.is_file()):
        digest.update(path.name.encode() + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def probe(directory: Path) -> list[str]:
    out: list[str] = []
    started = time.perf_counter()
    TF = Fabric(locations=str(directory), silent="deep")
    api: Any = TF.load("", silent="deep")
    sets = TF.explore(silent="deep", show=True)
    explored = time.perf_counter()
    node_features = [f for f in sets["nodes"] if f != "otype"]
    edge_features = [e for e in sets["edges"] if e != "oslots"]
    TF.load(node_features + edge_features, add=True, silent="deep")
    loaded = time.perf_counter()

    otext = TF.features["otext"].metaData
    otypes = [level[0] for level in api.C.levels.data]
    out.append(f"# Schema probe: `{otext.get('dataset', directory.name)}` ({directory.name})\n")
    out.append(f"- text-fabric {version('text-fabric')}; written {otext.get('dateWritten', '?')}")
    out.append(f"- content sha256 of *.tf: `{content_digest(directory)}`")
    out.append(
        f"- metadata-only discovery {explored - started:.1f}s; "
        f"loading all features {loaded - explored:.1f}s"
    )
    out.append(f"- slot type `{api.F.otype.slotType}`, max node {api.F.otype.maxNode}")
    out.append(f"- object types: {', '.join(f'`{t}`' for t in otypes)}\n")

    otype_of = api.F.otype.v
    rows = []
    hazards: list[str] = []
    for feature in node_features:
        data_type = TF.features[feature].dataType
        by_type: dict[str, collections.Counter[Any]] = collections.defaultdict(collections.Counter)
        for node, value in api.Fs(feature).data.items():
            by_type[otype_of(node)][value] += 1
        for otype, counts in sorted(by_type.items()):
            total = api.F.otype.sInterval(otype)
            covered = sum(counts.values())
            n_total = total[1] - total[0] + 1 if total else covered
            values = list(counts)
            empty = counts.get("", 0) if data_type == "str" else 0
            non_nfc = sum(
                1 for v in values if isinstance(v, str) and unicodedata.normalize("NFC", v) != v
            )
            escaped = sum(1 for v in values if isinstance(v, str) and any(c in v for c in ESCAPED))
            rows.append(
                (feature, otype, data_type, len(values), n_total - covered, empty, non_nfc, escaped)
            )
        if not SAFE_NAME.fullmatch(feature):
            hazards.append(f"feature name `{feature}` is not expressible in a template")
        if feature in otypes:
            hazards.append(f"feature `{feature}` has the same name as an object type")

    out.append("## Node features per object type\n")
    out.append(
        "| feature | type | dtype | distinct | bucket "
        "| no value | empty str | non-NFC | needs escape |"
    )
    out.append("|---|---|---|---:|---|---:|---:|---:|---:|")
    for feature, otype, dt, k, missing, empty, non_nfc, esc in sorted(
        rows, key=lambda r: (r[3], r[0], r[1])
    ):
        out.append(
            f"| `{feature}` | `{otype}` | {dt} | {k} | {bucket(k)} "
            f"| {missing} | {empty} | {non_nfc} | {esc} |"
        )

    out.append("\n## Bucket summary (feature, object type) pairs\n")
    summary = collections.Counter((bucket(r[3]), r[2]) for r in rows)
    out.append("| bucket | str | int |")
    out.append("|---|---:|---:|")
    for _, name in (*BUCKETS, (0, ">2000")):
        out.append(f"| {name} | {summary[(name, 'str')]} | {summary[(name, 'int')]} |")

    out.append("\n## Edge features\n")
    out.append("| edge | values | (from type, to type): count |")
    out.append("|---|---|---|")
    for edge in edge_features:
        pairs: collections.Counter[tuple[str, str]] = collections.Counter()
        for source, targets in api.Es(edge).data.items():
            for target in targets:
                pairs[(otype_of(source), otype_of(target))] += 1
        meta = TF.features[edge]
        shown = "; ".join(f"{a}→{b}: {n}" for (a, b), n in pairs.most_common(6))
        out.append(f"| `{edge}` | {bool(meta.edgeValues)} | {shown} |")

    out.append("\n## Hazards\n")
    out.extend(f"- {h}" for h in hazards) if hazards else out.append("- none")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="a TF dataset directory (containing *.tf)")
    args = parser.parse_args(argv)
    print("\n".join(probe(args.directory.expanduser())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
