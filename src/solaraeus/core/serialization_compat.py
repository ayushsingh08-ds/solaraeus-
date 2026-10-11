"""Serialization backward-compatibility shim (Track-2 integrity-fixes).

Track-2 adds physical-unit suffixes to serialized dataclass fields and record
keys (e.g. ``tmrt_tolerance -> tmrt_tolerance_k``). Artifacts already committed
under ``results/`` were written with the OLD, unsuffixed keys. To keep those
frozen artifacts parseable without regenerating them, every rename is registered
here as ``new_key -> (old_key, ...)``.

Contract:
  * SAVE emits the NEW key only (producers are updated at their call sites).
  * LOAD accepts the new key AND any registered legacy alias, via the helpers
    below. Nothing in this module changes a numeric value; it only reconciles
    key spellings, so the golden master is unaffected.

This is deliberately a tiny, dependency-free module: the engine kernels never
import it, only the (de)serialization boundary does.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# new canonical key -> legacy aliases accepted on load (never emitted on save).
# Grows one entry per Track-2 rename commit.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "tmrt_tolerance_k": ("tmrt_tolerance",),
    "predicted_error_bound_k": ("predicted_error_bound",),
    "max_predicted_bound_k": ("max_predicted_bound",),
    "predicted_bound_k": ("predicted_bound",),
    "surface_temperature_k": ("surface_temperature",),
}


def legacy_aliases(new_key: str) -> tuple[str, ...]:
    """Legacy spellings accepted on load for ``new_key`` (empty if none)."""
    return FIELD_ALIASES.get(new_key, ())


def get_aliased(source: Any, new_key: str, default: Any = None) -> Any:
    """Read ``new_key`` from a dict or object, falling back to legacy aliases.

    Tries the canonical key first, then each registered legacy alias in order.
    Works on mappings (``dict``/CSV rows) and on attribute-bearing objects.
    Returns ``default`` if neither the new key nor any alias is present.
    """
    for key in (new_key, *legacy_aliases(new_key)):
        if isinstance(source, Mapping):
            if key in source:
                return source[key]
        else:
            sentinel = object()
            value = getattr(source, key, sentinel)
            if value is not sentinel:
                return value
    return default


def normalize_keys(data: Mapping[str, Any],
                   new_keys: Iterable[str] | None = None) -> dict[str, Any]:
    """Return a copy of ``data`` with legacy keys coalesced to canonical keys.

    For each registered rename, if the canonical key is absent but a legacy
    alias is present, the alias's value is copied under the canonical key. The
    original entries are left intact (non-destructive). Restrict the pass to
    ``new_keys`` when only some renames apply to this record type.
    """
    out = dict(data)
    targets = tuple(new_keys) if new_keys is not None else tuple(FIELD_ALIASES)
    for new_key in targets:
        if new_key in out:
            continue
        for alias in legacy_aliases(new_key):
            if alias in out:
                out[new_key] = out[alias]
                break
    return out
