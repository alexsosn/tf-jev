"""Experimental opt-in grounded planning; native TF/compiler remain authoritative."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from enum import Enum

from tf_jev.decisions import ChoiceQuestion
from tf_jev.ir import Atom, Predicate, PredicateOp, Query, RelationOp
from tf_jev.parser import (
    _RELATIONS,
    ParsePolicy,
    ParseStatus,
    SemanticParser,
    _Run,
    _Stop,
)
from tf_jev.schema import NodeFeature

GRAMMAR = (
    "Interpret ALL constraints using annotations and structure only. Supported: "
    "one typed node with up to three distinct feature predicates; two typed nodes "
    "with one listed relation, returning either/both in requested order; or parents "
    "without any matching contained child, one exclusion without nesting. "
    "Predicates: literal equality/inequality with 1-3 OR alternatives; annotation "
    "presence/absence; integer greater/less than an explicit integer. "
    "Unsupported: regex, feature-to-feature comparison, aggregation/counting, top-N, "
    "sorting, more than two nodes, more than three predicates per node, more than "
    "three alternatives, nested quantifiers, arbitrary Boolean expressions, "
    "semantics not represented by annotations. Native TF may support more than "
    "this compiler subset. Ambiguous means multiple unresolved interpretations."
)


@dataclass(frozen=True)
class Gate:
    probability: float = 0.8
    margin: float = 0.2

    def __post_init__(self) -> None:
        for value in (self.probability, self.margin):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("invalid stage gate")


@dataclass(frozen=True)
class GroundedPolicy(ParsePolicy):
    max_context_chars: int = 65536
    shape_gate: Gate | None = None
    type_gate: Gate | None = None
    feature_gate: Gate | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        for gate in (self.shape_gate, self.type_gate, self.feature_gate):
            if gate is not None and not isinstance(gate, Gate):
                raise ValueError("invalid stage policy")


@dataclass(frozen=True)
class GroundedParser(SemanticParser):
    policy: GroundedPolicy = GroundedPolicy()

    def __post_init__(self) -> None:
        if not isinstance(self.policy, GroundedPolicy):
            raise ValueError("grounded parser requires grounded policy")

    def _new_run(self, request: str) -> _Run:
        return _GroundedRun(self, request)


class _End(Enum):
    FEATURES = "stop_features"


def _json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, default=lambda x: x.value if isinstance(x, Enum) else None
    )


class _GroundedRun(_Run):
    def __init__(self, parser: GroundedParser, request: str) -> None:
        super().__init__(parser, request)
        self.focus: dict[str, object] = {}
        self._corpus: str | None = None
        self._candidate: str | None = None
        self._shape: str | None = None

    def gate(self, name: str) -> tuple[float, float]:
        policy = self.parser.policy
        assert isinstance(policy, GroundedPolicy)
        gate = (
            policy.shape_gate
            if name == "shape"
            else policy.type_gate
            if name.endswith(".type")
            else policy.feature_gate
            if name.endswith(".feature")
            else None
        )
        return (gate.probability, gate.margin) if gate is not None else super().gate(name)

    def corpus(self) -> str:
        if self._corpus is None:
            schema = self.parser.schema
            if any(
                len(items) > self.parser.policy.max_symbols
                for items in (
                    schema.object_type_details,
                    schema.node_features,
                    schema.edge_features,
                )
            ):
                raise _Stop(ParseStatus.UNSUPPORTED, "choice_budget")
            # Refuse oversized metadata before constructing escaped copies.
            raw_size = sum(len(f.name) + len(f.description or "") for f in schema.node_features)
            raw_size += sum(len(f.name) + len(f.description or "") for f in schema.edge_features)
            if raw_size > self.parser.policy.max_context_chars:
                raise _Stop(ParseStatus.UNSUPPORTED, "context_budget")
            types = [
                dict(
                    name=t.name,
                    role="slot" if t.slot else "non-slot",
                    attested_features=[
                        f.name
                        for f in schema.node_features
                        if schema.domain(f.name, t.name).missing_count
                        < schema.domain(f.name, t.name).node_count
                    ],
                )
                for t in schema.object_type_details
                if t.expressible
            ]
            self._corpus = _json(
                dict(
                    types=types,
                    features=[
                        dict(name=f.name, dtype=f.dtype, description=f.description)
                        for f in schema.node_features
                    ],
                    edges=[
                        dict(name=f.name, description=f.description) for f in schema.edge_features
                    ],
                )
            )
        return self._corpus

    def context(self) -> dict[str, str]:
        context = super().context()
        context.update(
            corpus=self.corpus(),
            grammar=GRAMMAR,
            operators=_json([p.value for p in PredicateOp]),
            relations=_json({r.value: _RELATIONS[r] for r in RelationOp}),
            focus=_json(self.focus),
            roles="For containment/exclusion node 0 is the returned parent and node 1 "
            "the child witness. Otherwise plan two distinct roles in mention order; "
            "output projection later chooses requested columns/order. "
            "A constraint on a witness does not constrain its parent.",
        )
        if self._candidate is not None:
            context["candidate"] = self._candidate
        return context

    def context_size(
        self, context: dict[str, str], question: ChoiceQuestion, descriptions: list[str]
    ) -> int:
        wire = dict(
            state=context,
            questions={
                "decision": dict(
                    type="choice",
                    instructions=question.prompt,
                    criteria={o.label: o.description for o in question.options},
                )
            },
            model="x" * 128,
        )
        return len(_json(wire).encode("utf8"))

    def shape(self) -> str:
        self._shape = self.choose(
            "shape",
            "Choose the COMPLETE request structure under the stated corpus and grammar. "
            "Do not omit constraints or resolve unstated references by guessing.",
            [
                ("atom", "atom: One node type filtered by annotations."),
                ("relation", "relation: Two typed nodes connected by one relation."),
                ("without", "without: Parents with no matching contained child."),
                ("ambiguous", "ambiguous: Multiple unresolved meanings or unstated references."),
                ("unsupported", "unsupported: The complete request exceeds these capabilities."),
            ],
        )
        return self._shape

    def atom(self, index: int) -> Atom:
        prefix = f"atom{index}"
        self.focus = dict(index=index, shape=self._shape)
        kind = self.choose(
            prefix + ".type",
            f"Select the type for node role {index}. Use the stated parent/witness roles.",
            [
                (t.name, _json(dict(name=t.name, role="slot" if t.slot else "non-slot")))
                for t in self.parser.schema.object_type_details
                if t.expressible
            ],
        )
        predicates: list[Predicate] = []
        for i in range(4):
            self.focus = dict(
                index=index,
                object_type=kind,
                predicates=[asdict(p) for p in predicates],
                shape=self._shape,
            )
            available = [
                f
                for f in self.parser.schema.node_features
                if f.name not in {p.feature for p in predicates}
            ]
            options: list[tuple[NodeFeature | _End, str]] = [
                (
                    f,
                    _json(
                        dict(
                            kind="feature",
                            name=f.name,
                            dtype=f.dtype,
                            description=f.description,
                            attested_on_type=self.parser.schema.domain(f.name, kind).missing_count
                            < self.parser.schema.domain(f.name, kind).node_count,
                        )
                    ),
                )
                for f in available
            ]
            options.append(
                (
                    _End.FEATURES,
                    _json(
                        dict(
                            kind="stop",
                            meaning="All required features on THIS node "
                                    "have already been selected.",
                        )
                    ),
                )
            )
            stage = prefix + f".pred{i}"
            feature = self.choose(
                stage + ".feature",
                "Select any additional feature REQUIRED to express a constraint on this "
                "node. Select stop only when none remains. Do not transfer witness "
                "constraints to the parent. Never invent constraints.",
                options,
            )
            if feature is _End.FEATURES:
                return Atom(kind, tuple(predicates))
            if i == 3:
                raise _Stop(ParseStatus.UNSUPPORTED, "predicate_budget")
            assert isinstance(feature, NodeFeature)
            predicates.append(self.predicate(kind, feature, stage))
        raise AssertionError("bounded feature loop")

    def candidate(self, query: Query, projection: tuple[int, ...]) -> None:
        self.focus = {}
        self._candidate = _json(dict(query=asdict(query), projection=projection))
