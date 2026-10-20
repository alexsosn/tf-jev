"""Opt-in bounded candidate proposals with complete-candidate fidelity verification."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeVar

from tf_jev.compiler import CompileError, compile_query
from tf_jev.grounded import GRAMMAR, GroundedParser, _GroundedRun, _json
from tf_jev.ir import Parent, PredicateOp, Query
from tf_jev.parser import _RELATIONS, ParseStatus, _Run, _safe_description, _Stop
from tf_jev.schema import CorpusSchema

T = TypeVar("T")
OPERATORS = {
    PredicateOp.EQ: "annotation equals the requested literal value(s)",
    PredicateOp.NE: "annotation does not equal any of the requested literal value(s)",
    PredicateOp.PRESENT: "annotation exists, regardless of its value",
    PredicateOp.ABSENT: "annotation is missing on the node",
    PredicateOp.GT: "integer annotation is greater than the stated integer",
    PredicateOp.LT: "integer annotation is less than the stated integer",
}


@dataclass(frozen=True)
class CandidateParser(GroundedParser):
    """Experimental parser; only complete-candidate fidelity has probability gates.

    Result confidence still reports the weakest selected proposal probability;
    it is not calibrated whole-query confidence. All choices/evidence are retained.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if any(
            g is not None
            for g in (self.policy.shape_gate, self.policy.type_gate, self.policy.feature_gate)
        ):
            raise ValueError("candidate parser does not accept per-stage gates")

    def _new_run(self, request: str) -> _Run:
        return _CandidateRun(self, request)


class _CandidateRun(_GroundedRun):
    stage = ""
    _meaning: str | None = None

    def context(self) -> dict[str, str]:
        context = _Run.context(self)
        if self.stage == "verify":
            assert self._candidate is not None and self._meaning is not None
            return dict(
                request=self.request,
                contract=context["contract"],
                grammar=GRAMMAR,
                candidate=self._candidate,
                candidate_meaning=self._meaning,
            )
        if self.stage.endswith(".type"):
            type_context = {
                "request": context["request"],
                "contract": context["contract"],
                "types": _json(json.loads(self.corpus())["types"]),
            }
            if self.focus["index"] == 1:
                type_context["planned_first_type"] = self.state["atom0.type"]
                type_context["target_role"] = (
                    "child witness" if self._shape == "without" else "second related node"
                )
            return type_context
        if self.stage.endswith(".count"):
            f = json.loads(self.state[self.stage.removesuffix(".count") + ".feature"])
            return dict(
                request=self.request,
                contract=context["contract"],
                object_type=str(self.focus["object_type"]),
                property_id=f["name"],
                property_meaning=_safe_description(f["description"] or f["name"]),
                role=_scope(self._shape, self.focus["index"]),
            )
        if self.stage in ("shape", "verify"):
            context["grammar"] = GRAMMAR
        if self.stage != "shape":
            context["roles"] = (
                "For containment/exclusion role 0 is the returned "
                "parent and role 1 the child witness. Otherwise roles "
                "follow mention order. A witness constraint does not "
                "constrain its parent."
            )
            context["focus"] = _json(self.focus)
        if self._candidate is not None:
            context["candidate"] = self._candidate
        return context

    def shape(self) -> str:
        self._shape = self.choose(
            "shape",
            (
                "Route the structural pattern of the request. An unfamiliar "
                "literal does not change the pattern: code checks "
                "actual annotation/value membership later. Distinguish "
                "returned columns from additional related witness "
                "nodes."
            ),
            [
                (
                    "atom",
                    (
                        "atom: One entity node with only its OWN annotation "
                        "conditions. NO second-node relationship or witness "
                        "condition."
                    ),
                ),
                (
                    "relation",
                    (
                        "relation: A POSITIVE relationship between two nodes, "
                        "including containment or immediate adjacency. Types "
                        "may be identical; return one node or ordered pairs. "
                        "A returned parent containing a child uses this."
                    ),
                ),
                (
                    "without",
                    (
                        "without: Return parent nodes with NO matching contained "
                        "child. This is negative containment, not a positive "
                        "relationship."
                    ),
                ),
                (
                    "ambiguous",
                    (
                        "ambiguous: Unresolved object kind, meaning, reference "
                        "or scope with multiple plausible interpretations."
                    ),
                ),
                (
                    "unsupported",
                    (
                        "unsupported: Outside the stated grammar, such as "
                        "regex, aggregation/counting, sorting, nested quantifiers "
                        "or more than two nodes."
                    ),
                ),
            ],
        )
        return self._shape

    def gate(self, name: str) -> tuple[float, float]:
        if name != "verify":
            return (0.0, 0.0)
        return super().gate(name)

    def choose(self, name: str, prompt: str, options: list[tuple[T, str]]) -> T:
        self.stage = name
        if name == "verify":
            prompt = (
                "Does candidate_meaning, the deterministic explanation "
                "of candidate, exactly express ALL request restrictions "
                "and output roles? Reject any missing/invented condition, "
                "broader alternative values, wrong scope/direction/columns "
                "or unsupported operation. The candidate was proposed, "
                "not assumed correct."
            )
            options = [
                (
                    v,
                    "yes: exact complete match of every requirement and output role"
                    if v == "yes"
                    else "no: any missing, extra, contradictory, broader or unsupported meaning",
                )
                for v, _ in options
            ]
        if name.endswith(".type"):
            role = self.focus["index"]
            assert isinstance(role, int)
            target = (
                ("returned parent" if role == 0 else "excluded child witness")
                if self._shape == "without"
                else ("first-mentioned node" if role == 0 else "second-mentioned node")
                if self._shape == "relation"
                else None
            )
            prompt = "Which corpus object type is being requested"
            prompt += f" for the {target}?" if target else "?"
            if role == 1:
                prompt = (
                    (
                        "Select the native object type of the excluded child "
                        "witness, NOT its returned parent."
                    )
                    if self._shape == "without"
                    else (
                        "Select the native object type of the second related "
                        "node (the witness), which is not necessarily the "
                        "returned node."
                    )
                )
                prompt += " The two node roles may have identical types."
            options = [(v, json.loads(d)["name"]) for v, d in options]
        if name.endswith(".operator"):
            feature = json.loads(self.state[name.removesuffix(".operator") + ".feature"])
            prompt = (
                f"For node role {self.focus['index']} of type {self.focus['object_type']}, "
                f"what comparison does the request require on annotation "
                f"{feature['name']}? Choose the meaning, not the symbol. "
                f"Presence means an annotation exists; absence means "
                f"it is missing, not a sentinel literal."
            )
            options = [
                (value, f"{description}: {OPERATORS[value]}")
                if isinstance(value, PredicateOp)
                else (value, description)
                for value, description in options
            ]
        if name.endswith(".count"):
            f = json.loads(self.state[name.removesuffix(".count") + ".feature"])
            scope = _scope(self._shape, self.focus["index"])
            prompt = _safe_description(
                f"How many OR-alternative values are requested for "
                f"annotation {f['name']} ({f['description'] or f['name']}) "
                f"on the {scope} of type {self.focus['object_type']}? "
                f"Count values of THIS property on THIS node only, "
                f"not values for other properties/nodes."
            )
            options = [
                (v, f"{d}: exactly {d} OR-alternative value(s) for this property on this node")
                for v, d in options
            ]
        proposal = super().choose(name, prompt, options)
        return proposal

    def candidate(self, query: Query, projection: tuple[int, ...]) -> None:
        super().candidate(query, projection)
        try:
            self._meaning = candidate_meaning(query, projection, self.parser.schema)
        except CompileError:
            raise _Stop(ParseStatus.UNSUPPORTED, "compiler_rejected") from None


def _scope(shape: str | None, index: object) -> str:
    if shape == "without":
        return "returned parent" if index == 0 else "excluded child witness"
    if shape == "relation":
        return "first-mentioned node" if index == 0 else "second-mentioned node"
    return "requested output node"


def candidate_meaning(query: Query, projection: tuple[int, ...], schema: CorpusSchema) -> str:
    """Deterministic explanation of validated IR, never an execution language."""
    compile_query(query, schema)
    if (
        not projection
        or any(type(i) is not int or not 0 <= i < len(query.atoms) for i in projection)
        or len(set(projection)) != len(projection)
    ):
        raise ValueError("invalid projection")
    features = {f.name: f for f in schema.node_features}
    edges = {f.name: f for f in schema.edge_features}
    lines = [
        "Return distinct output columns in this order: "
        + ", ".join(f"node{i}" for i in projection)
        + ". All other nodes are witnesses."
    ]
    meanings = {
        PredicateOp.EQ: "equals one of",
        PredicateOp.NE: "does not equal any of",
        PredicateOp.PRESENT: "must be present, including empty strings",
        PredicateOp.ABSENT: "must be missing",
        PredicateOp.GT: "is greater than",
        PredicateOp.LT: "is less than",
    }

    def describe(q: Query, prefix: str, parent: str | None) -> None:

        def label(ref: int | Parent) -> str:
            if ref is Parent.REF:
                assert parent is not None
                return parent
            return f"{prefix}node{ref}"

        for i, atom in enumerate(q.atoms):
            node = label(i)
            lines.append(f"{node} is a corpus node of type {_json(atom.object_type)}.")
            if atom.predicates:
                lines.append(f"ALL of these annotation conditions must hold on {node} itself:")
            for p in atom.predicates:
                f = features[p.feature]
                text = (
                    f"  {node}: annotation {_json(f.name)} "
                    f"(meaning {_json(f.description or f.name)}) "
                    f"{meanings[p.operator]}"
                )
                if p.values:
                    text += " " + (
                        _json(p.values[0])
                        if p.operator in (PredicateOp.GT, PredicateOp.LT)
                        else _json(sorted(set(p.values)))
                    )
                if p.operator is PredicateOp.NE:
                    text += "; missing annotations also match"
                lines.append(text + ".")
        for r in q.relations:
            source, target = (label(r.source), label(r.target))
            meaning = _RELATIONS[r.operator].replace("atom 0", source).replace("atom 1", target)
            text = f"Required relation with source {source} and target {target}: {meaning}"
            if r.edge is not None:
                text += (
                    f"; native edge feature {_json(r.edge)} "
                    f"(meaning {_json(edges[r.edge].description or r.edge)})"
                )
            if r.distance is not None:
                text += f"; explicit distance tolerance {r.distance}"
            lines.append(text + ".")
        for i, excluded in enumerate(q.without):
            lines.append(
                f"There must be NO matching combination of these child "
                f"witnesses for parent {label(excluded.parent)}:"
            )
            describe(excluded.body, f"{prefix}excluded{i}.", label(excluded.parent))

    describe(query, "", None)
    return "\n".join(lines)
