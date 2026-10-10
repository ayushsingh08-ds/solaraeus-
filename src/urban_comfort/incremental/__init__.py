"""
Incremental computation subpackage for dependency tracking, caching, certificates, and updates.
"""

from urban_comfort.incremental.affected_region import (
    AffectedRegionResult,
    compute_candidate_affected_region,
    project_box_shadow,
)
from urban_comfort.incremental.cache import (
    FieldMetadata,
    SimulationCache,
    compute_config_hash,
    compute_scene_hash,
    compute_weather_hash,
)
from urban_comfort.incremental.certificate import (
    CertificateVerification,
    CertificateViolationError,
    ErrorCertificate,
    generate_error_certificate,
    verify_certificate,
)
from urban_comfort.incremental.dependency_graph import (
    DEPENDENCY_EDGES,
    EDIT_TRIGGER_MAP,
    DependencyGraph,
)
from urban_comfort.incremental.mesh_affected_region import (
    compute_mesh_candidate_affected_region,
    project_mesh_shadow,
)
from urban_comfort.incremental.mesh_update import (
    AddMeshEdit,
    AddMultiMeshEdit,
    ChangeMeshHeightEdit,
    MoveMeshEdit,
    RemoveMeshEdit,
    ReplaceMeshEdit,
)
from urban_comfort.incremental.update import (
    AddBuildingEdit,
    ChangeHeightEdit,
    GeometricEdit,
    IncrementalUpdateResult,
    MoveBuildingEdit,
    RemoveBuildingEdit,
    incremental_update_certified,
    incremental_update_exact,
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
