"""Profile TF core loading and exact CorpusSchema extraction, without mutation.

Usage: python -m scripts.profile_schema path/to/tf/2021 [--output profile.json]
Metrics are measurements for *one process*, not an isolated allocation count.
No corpus text, literal values, node IDs, credentials or source paths are output.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

from tf_jev.schema import extract_schema


def _current_rss_bytes() -> int | None:
    """Read whole-process current RSS on Linux; avoid adding optional dependencies."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        for row in Path("/proc/self/status").read_text().splitlines():
            if row.startswith("VmRSS:"):
                parts = row.split()
                if len(parts) == 3 and parts[2] == "kB":
                    return int(parts[1]) * 1024
    except (OSError, ValueError):
        return None
    return None


def _peak_rss_bytes() -> int | None:
    """Whole-process high-water mark, Linux only. Not extractor peak allocation."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except (ImportError, OSError, ValueError):
        return None


def profile_schema(directory: Path, *, trace_python: bool = False) -> dict[str, object]:
    """One TF session, measured in two serial phases; no corpus text in results."""
    if not isinstance(directory, Path) or not directory.is_dir() or not (
        directory / "otype.tf"
    ).is_file():
        raise ValueError("a readable Text-Fabric corpus directory is required")
    if type(trace_python) is not bool:
        raise ValueError("trace_python must be a boolean")

    load_started = time.perf_counter()
    tf = Fabric(locations=str(directory), silent="deep")
    api: Any = tf.load("", silent="deep")
    if not api:
        raise ValueError("could not load Text-Fabric corpus")
    loaded_at = time.perf_counter()
    rss_at_load = _current_rss_bytes()

    traced_peak: int | None = None
    if trace_python:
        tracemalloc.start()
    try:
        schema = extract_schema(api)
        finished_at = time.perf_counter()
        if trace_python:
            traced_peak = tracemalloc.get_traced_memory()[1]
    finally:
        if trace_python:
            tracemalloc.stop()
    return {
        "format_version": 1,
        "tf_version": schema.identity.tf_version,
        "dataset": schema.identity.dataset,
        "version_dir": schema.identity.version_dir,
        "identity_key": schema.identity.key,
        "loaded_sha256": schema.identity.loaded_sha256,
        "object_types": len(schema.object_types),
        "node_features": len(schema.node_features),
        "edge_features": len(schema.edge_features),
        "load_seconds": round(loaded_at - load_started, 6),
        "extract_seconds": round(finished_at - loaded_at, 6),
        "rss_bytes_at_load": rss_at_load,
        "rss_bytes_after_extract": _current_rss_bytes(),
        "peak_process_rss_bytes": _peak_rss_bytes(),
        "trace_python": trace_python,
        "python_traced_peak_bytes": traced_peak,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="directory of local .tf features")
    parser.add_argument("--output", type=Path, help="write JSON output to this file")
    parser.add_argument(
        "--trace-python", action="store_true",
        help="trace Python allocations (small corpora only; perturbs performance)",
    )
    args = parser.parse_args(argv)
    report = profile_schema(args.directory.expanduser(), trace_python=args.trace_python)
    content = json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False) + chr(10)
    if args.output is None:
        print(content, end="")
    else:
        # Avoid partially written reference results if the process is interrupted.
        output: Path = args.output
        tmp = output.with_name(output.name + ".tmp")
        tmp.write_text(content, encoding="utf8")
        tmp.replace(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
