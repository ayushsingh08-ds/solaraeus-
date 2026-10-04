"""
Explicit dependency graph tracking data flow from input parameters to microclimatic fields.
Enables fine-grained, dependency-aware invalidation upon scene or weather modifications.
"""

from __future__ import annotations
from typing import Dict, List, Set, FrozenSet
from collections import defaultdict, deque


# Canonical field identifiers
FIELD_SHADOW = "shadow_mask"
FIELD_SVF = "svf"
FIELD_SHORTWAVE = "shortwave_flux"
FIELD_LONGWAVE = "longwave_flux"
FIELD_TMRT = "tmrt"
FIELD_UTCI = "utci"

INPUT_GEOMETRY = "building_geometry"
INPUT_SOLAR = "solar_position"
INPUT_ALBEDO = "material_albedo"
INPUT_THERMAL_MAT = "material_thermal"
INPUT_AIR_TEMP = "weather_air_temp"
INPUT_WIND = "weather_wind"
INPUT_HUMIDITY = "weather_humidity"
INPUT_DNI_DHI = "weather_radiation"

# Direct downstream adjacency list: parent -> children
DEPENDENCY_EDGES: Dict[str, List[str]] = {
    # Building geometry drives direct shadow and sky view factor
    INPUT_GEOMETRY: [FIELD_SHADOW, FIELD_SVF],
    # Solar position drives direct shadow and shortwave incidence
    INPUT_SOLAR: [FIELD_SHADOW, FIELD_SHORTWAVE],
    # DNI/DHI drives shortwave fluxes
    INPUT_DNI_DHI: [FIELD_SHORTWAVE],
    # Material albedo drives reflected shortwave
    INPUT_ALBEDO: [FIELD_SHORTWAVE],
    # Shadow and SVF feed into shortwave flux
    FIELD_SHADOW: [FIELD_SHORTWAVE],
    FIELD_SVF: [FIELD_SHORTWAVE, FIELD_LONGWAVE],
    # Thermal boundary inputs drive longwave emissions
    INPUT_THERMAL_MAT: [FIELD_LONGWAVE],
    INPUT_AIR_TEMP: [FIELD_LONGWAVE, FIELD_UTCI],
    INPUT_HUMIDITY: [FIELD_LONGWAVE, FIELD_UTCI],
    # Shortwave and longwave feed into Mean Radiant Temperature (Tmrt)
    FIELD_SHORTWAVE: [FIELD_TMRT],
    FIELD_LONGWAVE: [FIELD_TMRT],
    # Tmrt and microclimate variables feed into UTCI
    FIELD_TMRT: [FIELD_UTCI],
    INPUT_WIND: [FIELD_UTCI],
}

# Standard edit-to-input mapping
EDIT_TRIGGER_MAP: Dict[str, List[str]] = {
    "building_added": [INPUT_GEOMETRY],
    "building_removed": [INPUT_GEOMETRY],
    "building_height_changed": [INPUT_GEOMETRY],
    "building_moved": [INPUT_GEOMETRY],
    "solar_position_changed": [INPUT_SOLAR],
    "material_albedo_changed": [INPUT_ALBEDO],
    "material_thermal_changed": [INPUT_THERMAL_MAT],
    "weather_air_temp_changed": [INPUT_AIR_TEMP],
    "weather_wind_changed": [INPUT_WIND],
    "weather_humidity_changed": [INPUT_HUMIDITY],
    "weather_radiation_changed": [INPUT_DNI_DHI],
}


class DependencyGraph:
    """
    Manages the dependency graph of microclimate simulation fields.
    Performs forward reachability analysis to identify invalidated fields.
    """

    def __init__(self, edges: Dict[str, List[str]] = DEPENDENCY_EDGES):
        self.edges = edges
        # Reverse edges: child -> parents
        self.reverse_edges: Dict[str, List[str]] = defaultdict(list)
        for parent, children in self.edges.items():
            for child in children:
                self.reverse_edges[child].append(parent)

    def get_invalidated_fields(self, changed_inputs: List[str]) -> Set[str]:
        """
        Computes the complete set of downstream fields invalidated by modifications
        to the specified input variables.
        """
        invalidated = set()
        queue = deque(changed_inputs)

        while queue:
            node = queue.popleft()
            for child in self.edges.get(node, []):
                if child not in invalidated:
                    invalidated.add(child)
                    queue.append(child)

        return invalidated

    def get_invalidated_for_edit(self, edit_type: str) -> Set[str]:
        """
        Resolves invalidated fields for a named atomic edit operation.
        """
        changed_inputs = EDIT_TRIGGER_MAP.get(edit_type, [])
        if not changed_inputs:
            raise ValueError(f"Unknown edit type '{edit_type}'. Supported: {list(EDIT_TRIGGER_MAP.keys())}")
        return self.get_invalidated_fields(changed_inputs)

    def get_upstream_dependencies(self, field_name: str) -> Set[str]:
        """
        Returns all recursive upstream inputs and fields that contribute to a target field.
        """
        upstream = set()
        queue = deque([field_name])

        while queue:
            node = queue.popleft()
            for parent in self.reverse_edges.get(node, []):
                if parent not in upstream:
                    upstream.add(parent)
                    queue.append(parent)

        return upstream
