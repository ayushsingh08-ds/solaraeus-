"""Urban Comfort: Certified Incremental SOLWEIG-Compatible Urban Thermal-Comfort Engine.

The version is single-sourced from the installed distribution metadata so that
``pyproject.toml`` is the only place a release number is written. When the
package is imported straight from a source checkout without being installed,
the value falls back to ``"0.0.0+unknown"`` rather than raising.
"""

from __future__ import annotations

try:  # pragma: no cover - exercised implicitly on every import
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _distribution_version

    try:
        __version__ = _distribution_version("solaraeus")
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"
except ImportError:  # pragma: no cover - Python < 3.8
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
