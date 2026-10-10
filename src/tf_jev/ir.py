"""Typed, backend-independent IR for the researched prototype TF subset."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PredicateOp(Enum):
    EQ = "="
    NE = "#"
    PRESENT = "present"
    ABSENT = "absent"
    GT = ">"
    LT = "<"


class RelationOp(Enum):
    EMBEDS = "[["
    EMBEDDED_IN = "]]"
    SAME_SLOTS = "=="
    OVERLAP = "&&"
    DISJOINT = "||"
    SAME_START = "=:"
    SAME_END = ":="
    SAME_BOUNDARIES = "::"
    BEFORE = "<<"
    AFTER = ">>"
    ADJACENT_BEFORE = "<:"
    ADJACENT_AFTER = ":>"
    NEAR_BEFORE = "near_before"
    NEAR_AFTER = "near_after"
    EDGE_FORWARD = "edge_forward"
    EDGE_BACKWARD = "edge_backward"
    EDGE_EITHER = "edge_either"


class Parent(Enum):
    REF = "parent"


@dataclass(frozen=True)
class Predicate:
    feature: str
    operator: PredicateOp
    values: tuple[str | int, ...] = ()


@dataclass(frozen=True)
class Atom:
    object_type: str
    predicates: tuple[Predicate, ...] = ()


@dataclass(frozen=True)
class Relation:
    source: int | Parent
    operator: RelationOp
    target: int | Parent
    edge: str | None = None
    distance: int | None = None


@dataclass(frozen=True)
class Query:
    atoms: tuple[Atom, ...]
    relations: tuple[Relation, ...] = ()
    without: tuple[Without, ...] = ()


@dataclass(frozen=True)
class Without:
    parent: int
    body: Query
