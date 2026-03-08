"""Replay conformance harness for deterministic runtime patch traces."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Dict, List, Mapping, Sequence

from runtime.runtime_stub import KairoRuntime


@dataclass(frozen=True)
class ReplayConformanceResult:
    source: str
    repeats: int
    signatures: List[str]
    conformance: bool
    mismatch_indices: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "repeats": self.repeats,
            "signatures": self.signatures,
            "conformance": self.conformance,
            "mismatch_indices": self.mismatch_indices,
        }


def _trace_for_source(source: str, env: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    runtime = KairoRuntime()
    patch = runtime.build_program_run_patch(source=source, env=env)
    runtime.apply_patch(patch)

    revision = runtime.state.revisions[runtime.state.head]  # type: ignore[index]
    ui_ops = runtime.replay_ui_timeline()

    return {
        "patch": patch,
        "graph": revision.graph,
        "ui_ops": ui_ops,
    }


def _signature(trace: Dict[str, Any]) -> str:
    payload = json.dumps(trace, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def evaluate_replay_conformance(
    source: str,
    repeats: int = 3,
    env: Mapping[str, Any] | None = None,
) -> ReplayConformanceResult:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    if not isinstance(repeats, int) or repeats < 2:
        raise ValueError("repeats must be an integer >= 2")

    signatures: List[str] = []
    for _ in range(repeats):
        signatures.append(_signature(_trace_for_source(source=source, env=env)))

    baseline = signatures[0]
    mismatch_indices = [idx for idx, value in enumerate(signatures) if value != baseline]
    return ReplayConformanceResult(
        source=source,
        repeats=repeats,
        signatures=signatures,
        conformance=len(mismatch_indices) == 0,
        mismatch_indices=mismatch_indices,
    )


def evaluate_batch_replay_conformance(
    sources: Sequence[str],
    repeats: int = 3,
    env: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    results = [evaluate_replay_conformance(source=source, repeats=repeats, env=env) for source in sources]
    failed = [result.to_dict() for result in results if not result.conformance]

    return {
        "repeats": repeats,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": [result.to_dict() for result in results],
        "conformance": len(failed) == 0,
    }
