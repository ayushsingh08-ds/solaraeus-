"""Pytest path setup for the test-only legacy SOLWEIG oracle.

The deterministic legacy SOLWEIG reference engine is a test fixture living under
``tests/oracle/legacy_solweig/`` (relocated from ``src/solaraeus/`` so the
``solaraeus`` package name is free for the live engine). Putting the oracle
directory on ``sys.path`` lets the oracle tests ``import legacy_solweig``
without installing or exposing it as a shipped package.
"""
import os
import sys

_ORACLE_DIR = os.path.join(os.path.dirname(__file__), "oracle")
if _ORACLE_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_DIR)
