"""Immutable, corpus-grounded schema snapshots for the deterministic compiler.

Extraction reads local TF sources and loads admissible features in the supplied
session. Full value inventories remain local; JSON is a summary, not a prompt.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal

ENUM_LIMIT = 32
_SYMBOL = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_@-]*")


class SchemaError(ValueError):
    """Invalid TF state, unavailable symbols/values, or stale retrieval handle."""


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _digest_record(digest: Any, value: object) -> None:
    data = _json(value).encode("utf8")
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)


def _source_digest(directory: Path) -> str | None:
    if not directory.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.glob("*.tf") if p.is_file()):
        name = path.name.encode("utf8")
        digest.update(len(name).to_bytes(8, "big") + name)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _metadata_text(metadata: Mapping[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if value is not None and type(value) is not str:
        raise SchemaError("schema metadata must be immutable text")
    return value


def _admissible(name: str) -> bool:
    return (
        bool(_SYMBOL.fullmatch(name))
        and name not in ("otype", "oslots")
        and not name.startswith("omap@")
    )


@dataclass(frozen=True)
class CorpusIdentity:
    tf_version: str
    dataset: str | None
    version_dir: str
    date_written: str | None
    locations: tuple[tuple[str, str | None], ...]
    loaded_sha256: str

    @property
    def key(self) -> str:
        return hashlib.sha256(_json(asdict(self)).encode("utf8")).hexdigest()


@dataclass(frozen=True)
class ObjectType:
    name: str
    slot: bool
    expressible: bool


@dataclass(frozen=True)
class Enumerated:
    values: tuple[tuple[str, int], ...]
    tag: Literal["enumerated"] = field(default="enumerated", init=False)

    @property
    def distinct(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class Large:
    distinct: int
    retrieval_handle: str
    tag: Literal["large"] = field(default="large", init=False)


@dataclass(frozen=True)
class IntRange:
    minimum: int | None
    maximum: int | None
    distinct: int
    tag: Literal["int"] = field(default="int", init=False)


@dataclass(frozen=True)
class ValueDomain:
    object_type: str
    node_count: int
    missing_count: int
    kind: Enumerated | Large | IntRange
    has_empty_string: bool
    non_nfc_count: int

    @property
    def distinct(self) -> int:
        return self.kind.distinct


@dataclass(frozen=True)
class NodeFeature:
    name: str
    dtype: Literal["str", "int"]
    description: str | None
    domains: tuple[ValueDomain, ...]


@dataclass(frozen=True)
class EdgeFeature:
    name: str
    dtype: Literal["str", "int"]
    has_values: bool
    description: str | None
    endpoints: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class _Inventory:
    feature: str
    object_type: str
    values: tuple[tuple[str | int, int], ...]
    members: frozenset[str | int]


@dataclass(frozen=True)
class CorpusSchema:
    identity: CorpusIdentity
    object_type_details: tuple[ObjectType, ...]
    node_features: tuple[NodeFeature, ...]
    edge_features: tuple[EdgeFeature, ...]
    excluded_features: tuple[str, ...]
    _inventories: tuple[_Inventory, ...] = field(repr=False)

    @property
    def object_types(self) -> tuple[str, ...]:
        return tuple(t.name for t in self.object_type_details)

    @property
    def reserved_names(self) -> frozenset[str]:
        return frozenset(self.object_types)

    @property
    def type_named_features(self) -> frozenset[str]:
        return self.reserved_names.intersection(f.name for f in self.node_features)

    def object_type(self, name: str) -> ObjectType:
        for item in self.object_type_details:
            if item.name == name and item.expressible:
                return item
        raise SchemaError("unknown or inexpressible object type")

    def node_feature(self, name: str, object_type: str) -> NodeFeature:
        self.object_type(object_type)
        for item in self.node_features:
            if item.name == name:
                return item
        raise SchemaError("unknown or excluded node feature")

    def edge_feature(self, name: str) -> EdgeFeature:
        for item in self.edge_features:
            if item.name == name:
                return item
        raise SchemaError("unknown or excluded edge feature")

    def domain(self, feature: str, object_type: str) -> ValueDomain:
        node = self.node_feature(feature, object_type)
        return next(d for d in node.domains if d.object_type == object_type)

    def node_feature_type(self, feature: str, object_type: str) -> Literal["str", "int"]:
        return self.node_feature(feature, object_type).dtype

    def validate_value(self, feature: str, object_type: str, value: str | int) -> None:
        dtype = self.node_feature_type(feature, object_type)
        if type(value) is not (str if dtype == "str" else int):
            raise SchemaError("literal type differs from feature type")
        for inventory in self._inventories:
            if inventory.feature == feature and inventory.object_type == object_type:
                if value in inventory.members:
                    return
                break
        raise SchemaError("literal is absent from the exact corpus domain")

    def validate_edge(self, feature: str) -> None:
        self.edge_feature(feature)

    def retrieval_values(self, handle: str) -> tuple[tuple[str | int, int], ...]:
        for feature in self.node_features:
            for domain in feature.domains:
                if isinstance(domain.kind, Large) and domain.kind.retrieval_handle == handle:
                    return next(
                        i.values
                        for i in self._inventories
                        if i.feature == feature.name and i.object_type == domain.object_type
                    )
        raise SchemaError("unknown or stale retrieval handle")

    def to_json(self) -> str:
        """Deterministic local summary; omits unbounded value inventories."""
        return _json(
            {
                "identity": asdict(self.identity),
                "object_types": [asdict(t) for t in self.object_type_details],
                "node_features": [asdict(f) for f in self.node_features],
                "edge_features": [asdict(f) for f in self.edge_features],
                "excluded_features": self.excluded_features,
                "enum_limit": ENUM_LIMIT,
            }
        )


def extract_schema(api: Any) -> CorpusSchema:
    """Snapshot a stable loaded TF core session; never downloads or calls a model.

    Adds all admissible features to the session. Do not mutate the corpus or
    its source files concurrently. The returned snapshot is independent of any
    later mutations. Re-extract after updates before compiling new queries.
    """
    try:
        return _extract(api)
    except SchemaError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        raise SchemaError("invalid or unreadable Text-Fabric corpus state") from None


def _extract(api: Any) -> CorpusSchema:
    if not api:
        raise SchemaError("a loaded Text-Fabric core API is required")
    tf = api.TF
    sets = tf.explore(silent="deep", show=True)
    node_names = tuple(sorted(f for f in sets["nodes"] if _admissible(f)))
    edge_names = tuple(sorted(f for f in sets["edges"] if _admissible(f)))
    excluded = tuple(sorted(f for f in (*sets["nodes"], *sets["edges"]) if not _admissible(f)))
    if not tf.load((*node_names, *edge_names), add=True, silent="deep"):
        raise SchemaError("Text-Fabric could not load query features")
    types = tuple(
        ObjectType(level[0], level[0] == api.F.otype.slotType, bool(_SYMBOL.fullmatch(level[0])))
        for level in api.C.levels.data
    )
    node_types = dict(api.F.otype.items())
    totals = collections.Counter(node_types.values())
    if set(totals) != {t.name for t in types} or len(types) != len(totals):
        raise SchemaError("inconsistent object types")
    for object_type in types:
        interval = api.F.otype.sInterval(object_type.name)
        if (
            len(interval) != 2
            or interval[1] - interval[0] + 1 != totals[object_type.name]
            or any(
                node_types.get(n) != object_type.name for n in range(interval[0], interval[1] + 1)
            )
        ):
            raise SchemaError("native type interval differs from raw node types")
    loaded_digest = hashlib.sha256()
    _digest_record(loaded_digest, [asdict(t) for t in types])
    _digest_record(loaded_digest, ("otype", sorted(node_types.items())))
    _digest_record(
        loaded_digest, ("oslots", [(n, list(slots)) for n, slots in api.E.oslots.items()])
    )
    inventories: list[_Inventory] = []
    feature_meta: list[tuple[str, Literal["str", "int"], str | None]] = []
    for name in node_names:
        info = tf.features[name]
        dtype = info.dataType
        if dtype not in ("str", "int"):
            raise SchemaError("unsupported node feature type")
        description = _metadata_text(info.metaData, "description")
        _digest_record(
            loaded_digest, (name, dtype, info.metaData, sorted(api.Fs(name).data.items()))
        )
        by_type: dict[str, collections.Counter[str | int]] = collections.defaultdict(
            collections.Counter
        )
        for n, value in api.Fs(name).data.items():
            if n not in node_types or type(value) is not (str if dtype == "str" else int):
                raise SchemaError("invalid feature node or value type")
            by_type[node_types[n]][value] += 1
        for t in types:
            counts = by_type[t.name]
            inventories.append(
                _Inventory(name, t.name, tuple(sorted(counts.items())), frozenset(counts))
            )
        feature_meta.append((name, dtype, description))
    edges: list[EdgeFeature] = []
    for name in edge_names:
        info = tf.features[name]
        if info.dataType not in ("str", "int"):
            raise SchemaError("unsupported edge feature type")
        pairs: collections.Counter[tuple[str, str]] = collections.Counter()
        raw_edges = []
        for source, targets in sorted(api.Es(name).data.items()):
            if source not in node_types:
                raise SchemaError("edge source outside corpus")
            for target in targets:
                if target not in node_types:
                    raise SchemaError("edge target outside corpus")
                pairs[(node_types[source], node_types[target])] += 1
            raw_edges.append(
                (source, sorted(targets.items()) if info.edgeValues else sorted(targets))
            )
        _digest_record(
            loaded_digest, (name, info.dataType, bool(info.edgeValues), info.metaData, raw_edges)
        )
        edges.append(
            EdgeFeature(
                name,
                info.dataType,
                bool(info.edgeValues),
                _metadata_text(info.metaData, "description"),
                tuple((a, b, count) for (a, b), count in sorted(pairs.items())),
            )
        )
    locations = tuple(
        (str(path), _source_digest(path))
        for loc in tf.locations
        for mod in tf.modules
        for path in [Path(loc, mod).resolve()]
    )
    metadata = tf.features["otext"].metaData if "otext" in tf.features else {}
    _digest_record(loaded_digest, metadata)
    identity = CorpusIdentity(
        version("text-fabric"),
        _metadata_text(metadata, "dataset"),
        Path(tf.features["otype"].dirName).name,
        _metadata_text(metadata, "dateWritten"),
        locations,
        loaded_digest.hexdigest(),
    )
    features: list[NodeFeature] = []
    for name, dtype, description in feature_meta:
        domains = []
        for inventory in (i for i in inventories if i.feature == name):
            values = inventory.values
            kind: Enumerated | Large | IntRange
            if dtype == "int":
                integers = [v for v, _ in values if isinstance(v, int)]
                kind = IntRange(
                    min(integers) if integers else None,
                    max(integers) if integers else None,
                    len(integers),
                )
            elif len(values) <= ENUM_LIMIT:
                kind = Enumerated(tuple((v, count) for v, count in values if isinstance(v, str)))
            else:
                handle = hashlib.sha256(
                    _json((identity.key, name, inventory.object_type)).encode("utf8")
                ).hexdigest()
                kind = Large(len(values), handle)
            domains.append(
                ValueDomain(
                    inventory.object_type,
                    totals[inventory.object_type],
                    totals[inventory.object_type] - sum(count for _, count in values),
                    kind,
                    "" in inventory.members,
                    sum(
                        1
                        for v, _ in values
                        if isinstance(v, str) and unicodedata.normalize("NFC", v) != v
                    ),
                )
            )
        features.append(NodeFeature(name, dtype, description, tuple(domains)))
    return CorpusSchema(
        identity, types, tuple(features), tuple(edges), excluded, tuple(inventories)
    )
