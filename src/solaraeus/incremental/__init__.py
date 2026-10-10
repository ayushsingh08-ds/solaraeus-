"""
Incremental computation subpackage for dependency tracking, caching, certificates, and updates.
"""

from solaraeus.incremental.dependency_graph import (
    DependencyGraph, DEPENDENCY_EDGES, EDIT_TRIGGER_MAP
)
from solaraeus.incremental.cache import (
    SimulationCache, FieldMetadata,
    compute_scene_hash, compute_weather_hash, compute_config_hash
)
from solaraeus.incremental.update import (
    GeometricEdit, AddBuildingEdit, RemoveBuildingEdit,
    ChangeHeightEdit, MoveBuildingEdit,
    IncrementalUpdateResult, incremental_update_exact,
    incremental_update_certified
)
from solaraeus.incremental.affected_region import (
    AffectedRegionResult, compute_candidate_affected_region, project_box_shadow
)
from solaraeus.incremental.mesh_affected_region import (
    project_mesh_shadow, compute_mesh_candidate_affected_region
)
from solaraeus.incremental.mesh_update import (
    AddMeshEdit, AddMultiMeshEdit, RemoveMeshEdit, ReplaceMeshEdit, MoveMeshEdit, ChangeMeshHeightEdit
)
from solaraeus.incremental.certificate import (
    ErrorCertificate, CertificateVerification, CertificateViolationError,
    generate_error_certificate, verify_certificate
)

__all__ = [
    "DependencyGraph",
    "DEPENDENCY_EDGES",
    "EDIT_TRIGGER_MAP",
    "SimulationCache",
    "FieldMetadata",
    "compute_scene_hash",
    "compute_weather_hash",
    "compute_config_hash",
    "GeometricEdit",
    "AddBuildingEdit",
    "RemoveBuildingEdit",
    "ChangeHeightEdit",
    "MoveBuildingEdit",
    "AddMeshEdit",
    "AddMultiMeshEdit",
    "RemoveMeshEdit",
    "ReplaceMeshEdit",
    "MoveMeshEdit",
    "ChangeMeshHeightEdit",
    "IncrementalUpdateResult",
    "incremental_update_exact",
    "incremental_update_certified",
    "AffectedRegionResult",
    "compute_candidate_affected_region",
    "project_box_shadow",
    "project_mesh_shadow",
    "compute_mesh_candidate_affected_region",
    "ErrorCertificate",
    "CertificateVerification",
    "CertificateViolationError",
    "generate_error_certificate",
    "verify_certificate",
]
