"""Unit tests for the Track-2 serialization backward-compat shim."""
from __future__ import annotations

from solaraeus.core.serialization_compat import (
    FIELD_ALIASES,
    get_aliased,
    legacy_aliases,
    normalize_keys,
)


def test_tmrt_tolerance_alias_registered():
    assert "tmrt_tolerance" in legacy_aliases("tmrt_tolerance_k")


def test_get_aliased_prefers_new_key_from_dict():
    row = {"tmrt_tolerance_k": 0.5, "tmrt_tolerance": 9.9}
    assert get_aliased(row, "tmrt_tolerance_k") == 0.5


def test_get_aliased_falls_back_to_legacy_dict():
    legacy_row = {"tmrt_tolerance": 0.5}
    assert get_aliased(legacy_row, "tmrt_tolerance_k") == 0.5


def test_get_aliased_default_when_absent():
    assert get_aliased({}, "tmrt_tolerance_k", default=1.0) == 1.0


def test_get_aliased_on_object_attribute():
    class Rec:
        tmrt_tolerance_k = 0.5

    assert get_aliased(Rec(), "tmrt_tolerance_k") == 0.5


def test_get_aliased_on_legacy_object_attribute():
    class LegacyRec:
        tmrt_tolerance = 0.5

    assert get_aliased(LegacyRec(), "tmrt_tolerance_k") == 0.5


def test_normalize_keys_coalesces_legacy():
    out = normalize_keys({"tmrt_tolerance": 0.5})
    assert out["tmrt_tolerance_k"] == 0.5
    # non-destructive: original key retained
    assert out["tmrt_tolerance"] == 0.5


def test_normalize_keys_keeps_new_key_untouched():
    out = normalize_keys({"tmrt_tolerance_k": 0.5, "tmrt_tolerance": 9.9})
    assert out["tmrt_tolerance_k"] == 0.5


def test_every_alias_maps_to_distinct_new_key():
    seen: set[str] = set()
    for new_key, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            assert alias not in seen, f"alias {alias} registered twice"
            seen.add(alias)
            assert alias != new_key
