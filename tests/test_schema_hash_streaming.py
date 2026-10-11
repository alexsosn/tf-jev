"""RED-first exact digest and bounded allocation tests for BHSA hashing (#20)."""

from __future__ import annotations

import hashlib
import tracemalloc

import pytest

from tf_jev.schema import _digest_node_feature, _digest_record, _json


@pytest.mark.parametrize(
    ("metadata", "data"),
    [
        ({"valueType": "str", "description": "naïve e\u0301 | \\"}, {}),
        (
            {"z": "e\u0301", "a": "x\\y", "valueType": "str"},
            {4: " ", 2: "", 9: "x|y", 1: "e\u0301", 3: "line"},
        ),
        (
            {"description": "literal data", "valueType": "int"},
            {10: -121, 3: 0, 2: 210, 1: -1},
        ),
    ],
)
def test_hash_record_exact_compatibility(
    metadata: dict[str, str], data: dict[int, str | int]
) -> None:
    original = hashlib.sha256()
    _digest_record(original, ("feature", metadata["valueType"], metadata, sorted(data.items())))
    streamed = hashlib.sha256()
    _digest_node_feature(streamed, "feature", metadata["valueType"], metadata, data)
    assert streamed.digest() == original.digest()


def test_hash_record_multiple_chunks_ignore_mapping_order() -> None:
    original = {i: f"non-NFC-{i}-e\u0301|\\ space" for i in range(12_311, 0, -1)}
    reference = hashlib.sha256()
    _digest_record(reference, ("lex", "str", {"valueType": "str"}, sorted(original.items())))
    actual = hashlib.sha256()
    _digest_node_feature(actual, "lex", "str", {"valueType": "str"}, original)
    assert actual.hexdigest() == reference.hexdigest()
    reversed_order = dict(reversed(list(original.items())))
    again = hashlib.sha256()
    _digest_node_feature(again, "lex", "str", {"valueType": "str"}, reversed_order)
    assert again.digest() == reference.digest()


def test_peak_temporary_python_allocations_below_payload_size() -> None:
    data = {i: "long raw value: " + ("w|" * 120) + str(i) for i in range(1, 60_001)}
    payload_size = len(
        _json(("label", "str", {"valueType": "str"}, sorted(data.items()))).encode("utf8")
    )
    assert payload_size > 10_000_000
    tracemalloc.start()
    try:
        out = hashlib.sha256()
        _digest_node_feature(out, "label", "str", {"valueType": "str"}, data)
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    # This is an in-process Python temporary allocation bound, NOT RSS.
    assert peak < payload_size // 2


def test_corrupted_metadata_does_not_emit_partial_digest() -> None:
    # JSON must reject NaNs and other invalid metadata rather than losing hash identity.
    bad_metadata = {"score": float("nan")}
    with pytest.raises(ValueError):
        _digest_node_feature(hashlib.sha256(), "f", "str", bad_metadata, {1: "ok"})
