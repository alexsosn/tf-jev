"""Pure rendering of validated, schema-grounded IR into native TF search.

Compilation performs no TF execution or network calls. Schema extraction is a
separate concern; SymbolSchema is the narrow boundary required by the compiler.
"""

from __future__ import annotations

import re
from typing import Literal, Protocol

from .ir import Atom, Parent, Predicate, PredicateOp, Query, Relation, RelationOp, Without

K_MAX = 1000
_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_@-]*")
_EDGE_OPS = frozenset((RelationOp.EDGE_FORWARD, RelationOp.EDGE_BACKWARD, RelationOp.EDGE_EITHER))
_NEAR_OPS = frozenset((RelationOp.NEAR_BEFORE, RelationOp.NEAR_AFTER))

# Unicode `Cf` is not uniformly unsafe: joiners and LRM/RLM round-trip in
# actual TF corpora and support legitimate writing systems. Reject only format
# controls that obscure a query's visual contents or reverse apparent order.
# This is a native-query auditability policy, distinct from model prompt display.
_UNAUDITABLE_FORMAT_CONTROLS = (
    frozenset(chr(point) for point in (0x00AD, 0x200B, 0x2060, 0xFEFF))
    | frozenset(chr(point) for point in range(0x202A, 0x202F))
    | frozenset(chr(point) for point in range(0x2066, 0x206A))
)

class CompileError(ValueError):
    """Invalid/unsupported IR, unrepresentable value, or schema mismatch."""


class SymbolSchema(Protocol):
    @property
    def object_types(self) -> tuple[str, ...]: ...

    def node_feature_type(self, feature: str, object_type: str) -> Literal["str", "int"]: ...

    def validate_value(self, feature: str, object_type: str, value: str | int) -> None: ...

    def validate_edge(self, feature: str) -> None: ...


def _name(value: object, *, feature: bool = False) -> str:
    if type(value) is not str or not _NAME.fullmatch(value):
        raise CompileError("symbol is not expressible in native TF syntax")
    if feature and (value in ("otype", "oslots") or value.startswith("omap@")):
        raise CompileError("warp features are unsupported")
    return value


def _escape(value: str) -> str:
    if any(
        ord(c) < 32
        or ord(c) == 127
        or 0xD800 <= ord(c) <= 0xDFFF
        or c in _UNAUDITABLE_FORMAT_CONTROLS
        or (c.isspace() and c != " ")
        for c in value
    ):
        raise CompileError("unrepresentable literal value")
    return value.replace("\\", "\\\\").replace(" ", "\\ ").replace("|", "\\|")


def _predicate(predicate: Predicate, otype: str, schema: SymbolSchema) -> str:
    if type(predicate) is not Predicate or type(predicate.operator) is not PredicateOp:
        raise CompileError("predicate requires a closed operator")
    feature = _name(predicate.feature, feature=True)
    if type(predicate.values) is not tuple:
        raise CompileError("predicate values must be an immutable tuple")
    dtype = schema.node_feature_type(feature, otype)
    if dtype not in ("str", "int"):
        raise CompileError("unsupported feature type")
    op = predicate.operator
    if op in (PredicateOp.PRESENT, PredicateOp.ABSENT):
        if predicate.values:
            raise CompileError("presence/absence takes no values")
        return feature + ("#" if op is PredicateOp.ABSENT else "")
    if not predicate.values:
        raise CompileError("value predicate must be nonempty")
    if op in (PredicateOp.GT, PredicateOp.LT):
        if dtype != "int" or len(predicate.values) != 1 or type(predicate.values[0]) is not int:
            raise CompileError("integer bound requires one integer on an int feature")
        # A bound is a threshold, not a member of the observed corpus domain.
        return feature + str(op.value) + str(predicate.values[0])
    for value in predicate.values:
        if type(value) is not (str if dtype == "str" else int):
            raise CompileError("literal type differs from corpus feature type")
        schema.validate_value(feature, otype, value)
    values = sorted(set(predicate.values))
    encoded = "|".join(_escape(v) if isinstance(v, str) else str(v) for v in values)
    if values == [""]:
        encoded = "|"
    elif (
        op is PredicateOp.NE
        and len(values) == 1
        and isinstance(values[0], str)
        and values[0].isspace()
    ):
        # TF matches f# followed only by restored spaces as absence, before
        # considering value sets. Duplicate alternatives preserve the set.
        encoded = encoded + "|" + encoded
    return feature + str(op.value) + encoded


def _reference(value: int | Parent, count: int, body: bool) -> int | Parent:
    if value is Parent.REF and body:
        return value
    if type(value) is not int or not 0 <= value < count:
        raise CompileError("relation reference outside query scope")
    return value


def _operator(relation: Relation, schema: SymbolSchema) -> str:
    if type(relation) is not Relation or type(relation.operator) is not RelationOp:
        raise CompileError("relation requires a closed operator")
    op = relation.operator
    if op in _EDGE_OPS:
        if relation.distance is not None:
            raise CompileError("edge relation cannot carry distance")
        edge = _name(relation.edge, feature=True)
        schema.validate_edge(edge)
        if op is RelationOp.EDGE_FORWARD:
            return f"-{edge}>"
        if op is RelationOp.EDGE_BACKWARD:
            return f"<{edge}-"
        return f"<{edge}>"
    if relation.edge is not None:
        raise CompileError("non-edge relation cannot carry edge")
    if op in _NEAR_OPS:
        k = relation.distance
        if type(k) is not int or not 0 <= k <= K_MAX:
            raise CompileError(f"distance must be an integer in 0..{K_MAX}")
        return f"<{k}:" if op is RelationOp.NEAR_BEFORE else f":{k}>"
    if relation.distance is not None:
        raise CompileError("distance only supported on near relations")
    return op.value


def compile_query(query: Query, schema: SymbolSchema) -> str:
    """Compile the prototype subset; reject mismatches before emitting text.

    Atom order fixes output column order. Predicates, value sets and relation
    lines are canonicalized; successful compilation does not execute the query.
    """
    reserved = frozenset(schema.object_types)
    next_name = 0

    def allocate() -> str:
        nonlocal next_name
        while f"n{next_name}" in reserved:
            next_name += 1
        name = f"n{next_name}"
        next_name += 1
        return name

    def render(current: Query, *, body: bool = False) -> list[str]:
        if type(current) is not Query or any(
            type(items) is not tuple
            for items in (current.atoms, current.relations, current.without)
        ):
            raise CompileError("query requires immutable tuples")
        if not current.atoms:
            raise CompileError("empty query/body is unsupported")
        if body and current.without:
            raise CompileError("nested quantifiers are unsupported")
        quantifiers: dict[int, Without] = {}
        for quantifier in current.without:
            if type(quantifier) is not Without:
                raise CompileError("unsupported quantifier")
            parent = _reference(quantifier.parent, len(current.atoms), False)
            assert isinstance(parent, int)
            if parent in quantifiers:
                raise CompileError("only one without per parent is supported")
            quantifiers[parent] = quantifier
        names = [allocate() for _ in current.atoms]
        nodes: set[int | Parent] = set(range(len(names)))
        if body:
            nodes.add(Parent.REF)
        neighbors: dict[int | Parent, set[int | Parent]] = {n: set() for n in nodes}
        relation_lines: list[str] = []
        for relation in current.relations:
            operator = _operator(relation, schema)
            source = _reference(relation.source, len(names), body)
            target = _reference(relation.target, len(names), body)
            neighbors[source].add(target)
            neighbors[target].add(source)
            left = ".." if source is Parent.REF else names[source]
            right = ".." if target is Parent.REF else names[target]
            relation_lines.append(f"{left} {operator} {right}")
        visited: set[int | Parent] = set()
        todo: list[int | Parent] = [Parent.REF if body else 0]
        while todo:
            node = todo.pop()
            if node not in visited:
                visited.add(node)
                todo.extend(neighbors[node] - visited)
        if visited != nodes:
            raise CompileError("query graph must be connected (body includes parent)")
        lines: list[str] = []
        for index, atom in enumerate(current.atoms):
            if type(atom) is not Atom or type(atom.predicates) is not tuple:
                raise CompileError("atom requires immutable predicates")
            otype = _name(atom.object_type)
            if otype not in reserved:
                raise CompileError("unknown object type")
            features: set[str] = set()
            conditions: list[str] = []
            for predicate in atom.predicates:
                condition = _predicate(predicate, otype, schema)
                if predicate.feature in features:
                    raise CompileError("duplicate feature predicate; use one value set")
                features.add(predicate.feature)
                conditions.append(condition)
            conditions.sort()
            inline = [c for c in conditions if index not in quantifiers or "\\" not in c]
            continued = [c for c in conditions if index in quantifiers and "\\" in c]
            lines.append(" ".join([f"{names[index]}:{otype}", *inline]))
            if continued:
                lines.append("  " + " ".join(continued))
            if index in quantifiers:
                lines.append("/without/")
                lines.extend(render(quantifiers[index].body, body=True))
                lines.append("/-/")
        lines.extend(sorted(set(relation_lines)))
        return lines

    try:
        return "\n".join(render(query))
    except CompileError:
        raise
    except ValueError:
        # Do not propagate schema diagnostics, which may contain corpus text.
        raise CompileError("corpus schema rejected a symbol or value") from None
