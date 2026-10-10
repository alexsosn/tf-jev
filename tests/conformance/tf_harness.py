"""Test-only harness for running templates through the real Text-Fabric search.

This is evidence tooling for the grammar research (#2), not production API.
It mirrors how Text-Fabric's own ``A.search`` runs a query: ``S.search`` with a
list ``_msgCache`` so that diagnostics from the outer template *and* from every
quantifier sub-search are collected in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

# A tiny, fully synthetic corpus. Values are chosen to exercise escaping,
# Unicode, integer features, embedding, adjacency and edge features.
#
#   sentence s  : words 1..8
#   clause   c1 : words 1..4        clause c2 : words 5..8     (c2 -mother> c1)
#   phrase   p1 : 1,2 Time   p2 : 3 Pred   p3 : 4 Subj   p4 : 5,6 Objc   p5 : 7,8 PreC
WORDS: dict[int, dict[str, str | int]] = {
    1: {"lex": "B", "sp": "prep", "rank": 1},
    2: {"lex": "R>CJT/", "sp": "subs", "gn": "f", "nu": "sg", "rank": 2},
    3: {"lex": "BR>[", "sp": "verb", "gn": "m", "nu": "sg", "rank": 3},
    4: {"lex": ">LHJM/", "sp": "subs", "gn": "m", "nu": "pl", "rank": 4},
    5: {"lex": "a b", "sp": "subs", "gn": "f", "nu": "pl", "rank": 5},
    6: {"lex": "a|b", "sp": "verb", "gn": "f", "nu": "pl", "rank": 6},
    7: {"lex": "a\\b", "sp": "adjv", "rank": 7},
    8: {"lex": "בָּרָא", "sp": "verb", "gn": "m", "nu": "sg", "rank": 8},
}
PHRASES: dict[int, tuple[set[int], str]] = {
    9: ({1, 2}, "Time"),
    10: ({3}, "Pred"),
    11: ({4}, "Subj"),
    12: ({5, 6}, "Objc"),
    13: ({7, 8}, "PreC"),
}
CLAUSES: dict[int, set[int]] = {14: {1, 2, 3, 4}, 15: {5, 6, 7, 8}}
SENTENCE = 16


def build_tiny_corpus(directory: Path) -> None:
    otype: dict[int, str] = {n: "word" for n in WORDS}
    otype.update({n: "phrase" for n in PHRASES})
    otype.update({n: "clause" for n in CLAUSES})
    otype[SENTENCE] = "sentence"

    oslots: dict[int, set[int]] = {n: slots for (n, (slots, _)) in PHRASES.items()}
    oslots.update(CLAUSES)
    oslots[SENTENCE] = set(WORDS)

    node_features: dict[str, dict[int, Any]] = {"otype": otype}
    for feature in ("lex", "sp", "gn", "nu", "rank"):
        node_features[feature] = {n: w[feature] for (n, w) in WORDS.items() if feature in w}
    node_features["function"] = {n: f for (n, (_, f)) in PHRASES.items()}
    node_features["number"] = {n: i for (i, n) in enumerate([SENTENCE, *CLAUSES], start=1)}

    edge_features: dict[str, dict[int, Any]] = {
        "oslots": oslots,
        "mother": {15: {14}},
        "dist": {1: {2: 1, 3: 2}},
    }

    str_meta = {"valueType": "str"}
    int_meta = {"valueType": "int"}
    meta: dict[str, dict[str, Any]] = {
        "": {"createdBy": "tf-jev conformance fixture"},
        "otype": str_meta,
        "oslots": str_meta,
        "lex": str_meta,
        "sp": str_meta,
        "gn": str_meta,
        "nu": str_meta,
        "function": str_meta,
        "rank": int_meta,
        "number": int_meta,
        "mother": str_meta,
        "dist": {"valueType": "int", "edgeValues": True},
        "otext": {
            "sectionTypes": "sentence,clause",
            "sectionFeatures": "number,number",
            "fmt:text-orig-full": "{lex} ",
        },
    }
    TF = Fabric(locations=str(directory), silent="deep")
    TF.save(nodeFeatures=node_features, edgeFeatures=edge_features, metaData=meta, silent="deep")


def load_api(directory: Path, features: str | None = None) -> Any:
    TF = Fabric(locations=str(directory), silent="deep")
    if features is None:
        return TF.loadAll(silent="deep")
    return TF.load(features, silent="deep")


@dataclass(frozen=True)
class Outcome:
    """Result of running one template through real Text-Fabric search.

    ``ok`` is False whenever Text-Fabric reported *any* error, including
    errors from quantifier sub-searches that do not flip ``exe.good``.
    """

    ok: bool
    results: tuple[tuple[int, ...], ...] | None
    errors: tuple[str, ...]

    def error_text(self) -> str:
        return "\n".join(self.errors)


def run_template(api: Any, template: str, limit: int | None = None) -> Outcome:
    messages: list[Any] = []
    (results, status, _html, exe) = api.S.search(
        template, here=False, limit=limit, silent="deep", _msgCache=messages
    )
    errors = tuple(
        text
        for (is_error, _nl, raw) in (m for m in messages if isinstance(m, tuple))
        if is_error and (text := raw.strip())
    )
    ok = bool(status) and exe.good and not errors
    return Outcome(
        ok=ok,
        results=tuple(sorted(tuple(r) for r in results)) if ok else None,
        errors=errors,
    )
