"""Model-free, corpus-grounded Text-Fabric query compiler and native diagnostic CLI.

This narrow command accepts only a single validated QueryIR atom. It does not
interpret natural language or load a decision backend.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from tf.core.helpers import wrapMessages
from tf.fabric import Fabric

from .compiler import CompileError, compile_query
from .ir import Atom, Predicate, PredicateOp, Query
from .schema import SchemaError, extract_schema


class CliError(ValueError):
    """Static, safe diagnostic; never contains arbitrary corpus or model text."""


_INT = re.compile(r"[+-]?[0-9]+")
_MAX_LIMIT = 50_000


def _predicates(args: argparse.Namespace) -> tuple[list[tuple[str, PredicateOp, str | None]], tuple[str, ...]]:
    entries: list[tuple[str, PredicateOp, str | None]] = []
    for expression in args.eq:
        if "=" not in expression:
            raise CliError("invalid predicate syntax")
        name, value = expression.split("=", 1)
        if not name:
            raise CliError("invalid predicate syntax")
        entries.append((name, PredicateOp.EQ, value))
    entries.extend((name, PredicateOp.PRESENT, None) for name in args.present)
    entries.extend((name, PredicateOp.ABSENT, None) for name in args.absent)
    features = [name for name, _, _ in entries]
    if len(set(features)) != len(features):
        raise CliError("duplicate feature predicate")
    return entries, tuple(sorted(features))


def _native_count(api: Any, query: str, limit: int) -> int:
    """Count actual native TF tuples, never accept a cutoff or TF diagnostics."""
    messages: list[Any] = []
    try:
        rows, _status, _html, exe = api.S.search(
            query, here=False, limit=limit + 1, silent="deep", _msgCache=messages
        )
        count = 0
        for row in rows:
            if len(row) != 1 or type(row[0]) is not int:
                raise CliError("native result shape is invalid")
            count += 1
            if count > limit:
                raise CliError("native result limit exceeded")
        status, _html = wrapMessages(messages)
        if not status or not exe.good or any(
            bool(message[0]) for message in messages
            if isinstance(message, tuple) and len(message) >= 1
        ):
            raise CliError("native search rejected the query")
        return count
    except CliError:
        raise
    except Exception:
        raise CliError("native execution failed") from None


def _compile(args: argparse.Namespace) -> dict[str, object]:
    if args.limit is not None and not args.execute:
        raise CliError("--limit requires --execute")
    limit = 1000 if args.limit is None else args.limit
    if type(limit) is not int or not 1 <= limit <= _MAX_LIMIT:
        raise CliError("invalid result limit")
    entries, selected = _predicates(args)

    directory: Path = args.corpus.expanduser()
    if not directory.is_dir() or not (directory / "otype.tf").is_file():
        raise CliError("Text-Fabric corpus directory is unavailable")
    api: Any = Fabric(locations=str(directory), silent="deep").load("", silent="deep")
    if not api:
        raise CliError("Text-Fabric corpus could not be loaded")
    schema = extract_schema(api, node_features=selected, edge_features=())
    schema.object_type(args.object_type)

    predicates: list[Predicate] = []
    for feature, operator, literal in entries:
        if operator is PredicateOp.EQ:
            assert literal is not None
            dtype = schema.node_feature_type(feature, args.object_type)
            if dtype == "int":
                if _INT.fullmatch(literal) is None:
                    raise CliError("invalid integer feature value")
                value: str | int = int(literal)
            else:
                value = literal
            predicates.append(Predicate(feature, operator, (value,)))
        else:
            predicates.append(Predicate(feature, operator))
    query = compile_query(Query((Atom(args.object_type, tuple(predicates)),)), schema)

    report: dict[str, object] = {
        "query": query,
        "schema_key": schema.identity.key,
        "coverage_mode": schema.coverage.mode,
        "executed": bool(args.execute),
    }
    if args.execute:
        report["result_count"] = _native_count(api, query, limit)
        report["complete"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_subparsers(dest="command", required=True)
    compile_cli = actions.add_parser("compile", help="compile typed predicates against local TF")
    compile_cli.add_argument("--corpus", type=Path, required=True)
    compile_cli.add_argument("--type", dest="object_type", required=True)
    compile_cli.add_argument("--eq", action="append", default=[], metavar="FEATURE=VALUE")
    compile_cli.add_argument("--present", action="append", default=[], metavar="FEATURE")
    compile_cli.add_argument("--absent", action="append", default=[], metavar="FEATURE")
    compile_cli.add_argument("--execute", action="store_true", help="run native TF search")
    compile_cli.add_argument("--limit", type=int, help="maximum complete native result count")
    args = parser.parse_args(argv)
    try:
        report = _compile(args)
    except CliError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (SchemaError, CompileError, ValueError, OSError, TypeError, AttributeError, KeyError):
        print("error: invalid or unsupported corpus query", file=sys.stderr)
        return 2
    except Exception:
        print("error: Text-Fabric operation failed", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
