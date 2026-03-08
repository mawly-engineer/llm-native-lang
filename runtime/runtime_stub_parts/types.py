"""Shared data structures and errors for KAIRO runtime stub."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class Revision:
    id: str
    parent: str | None
    graph: Dict[str, Any]
    ui_revision: str | None = None


@dataclass
class RuntimeState:
    revisions: Dict[str, Revision] = field(default_factory=dict)
    head: str | None = None


@dataclass
class UITimelineEvent:
    id: str
    parent: str | None
    ops: List[Dict[str, Any]]
    secondary_parent: str | None = None
    resolution_notes: str | None = None
    merge_mode: str = "materialized"
    delta_base_revision: str | None = None


@dataclass
class UISnapshot:
    id: str
    event_head: str | None
    ops: List[Dict[str, Any]]


class PatchError(Exception):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        self.code = code
        self.details = details
        super().__init__(f"{code}: {message}")
