"""Rabbit Hole Archives detective mechanics as an out-of-tree Bunnyland plugin."""

from __future__ import annotations

from .actions import ACTION_DEFINITIONS, EXAMINE_EVIDENCE
from .case_import import CaseImportError, ImportedCase, import_case, imported_case_keys
from .components import (
    CANONICAL_COMPONENTS,
    COMPONENT_TYPES,
    EDGE_TYPES,
    MUTABLE_COMPONENTS,
    ArchiveCaseComponent,
    ArchiveEventComponent,
    ArchiveEvidenceComponent,
    ArchivePlaceComponent,
    ArchiveSuspectComponent,
    DiscoveredBy,
    DiscoveryComponent,
    DiscoveryOf,
    EvidenceFromEvent,
    InvestigatorSessionComponent,
    SealedSolutionComponent,
)
from .mechanics import (
    COMMAND_TYPE,
    EvidenceExaminedEvent,
    ExamineEvidenceHandler,
    apply_handler_result,
)
from .plugin import PLUGIN_ID, PLUGIN_VERSION, archive_plugin, bunnyland_plugins
from .projection import (
    ArchiveNarratorView,
    DiscoveredEvidenceView,
    ProjectionError,
    narrator_view,
)

__all__ = [
    "ACTION_DEFINITIONS",
    "CANONICAL_COMPONENTS",
    "COMMAND_TYPE",
    "COMPONENT_TYPES",
    "EDGE_TYPES",
    "EXAMINE_EVIDENCE",
    "MUTABLE_COMPONENTS",
    "PLUGIN_ID",
    "PLUGIN_VERSION",
    "ArchiveCaseComponent",
    "ArchiveEventComponent",
    "ArchiveEvidenceComponent",
    "ArchiveNarratorView",
    "ArchivePlaceComponent",
    "ArchiveSuspectComponent",
    "CaseImportError",
    "DiscoveredBy",
    "DiscoveredEvidenceView",
    "DiscoveryComponent",
    "DiscoveryOf",
    "EvidenceExaminedEvent",
    "EvidenceFromEvent",
    "ExamineEvidenceHandler",
    "ImportedCase",
    "InvestigatorSessionComponent",
    "ProjectionError",
    "SealedSolutionComponent",
    "apply_handler_result",
    "archive_plugin",
    "bunnyland_plugins",
    "import_case",
    "imported_case_keys",
    "narrator_view",
]
