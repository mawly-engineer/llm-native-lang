"""Compatibility shim for runtime stub symbols."""

from runtime.runtime_stub_parts import (
    KairoRuntime,
    PatchError,
    Revision,
    RuntimeState,
    UISnapshot,
    UITimelineEvent,
)

__all__ = ["KairoRuntime", "PatchError", "Revision", "RuntimeState", "UITimelineEvent", "UISnapshot"]
