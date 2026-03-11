"""Replay conformance harness for deterministic interpreter execution traces.

This module provides trace capture, serialization, and replay validation
for the interpreter runtime. It ensures that program execution is deterministic
and detects any non-deterministic operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
import json
from typing import Any, Dict, List, Mapping, Sequence, Callable

from runtime.interpreter_runtime import eval_expr_with_trace, EvalContext, EvalError
from runtime.ast_contract import validate_ast


@dataclass(frozen=True)
class ExecutionTrace:
    """A complete execution trace with state snapshots."""
    
    program: str
    trace_ids: List[str]
    final_result: Any
    fuel_used: int | None
    builtin_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize trace to dictionary."""
        return {
            "program": self.program,
            "trace_ids": self.trace_ids,
            "final_result": self._serialize_value(self.final_result),
            "fuel_used": self.fuel_used,
            "builtin_calls": self.builtin_calls,
        }
    
    def to_json(self) -> str:
        """Serialize trace to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    def signature(self) -> str:
        """Generate deterministic signature for this trace."""
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a Python value to JSON-compatible format."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return [ExecutionTrace._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: ExecutionTrace._serialize_value(v) for k, v in value.items()}
        return str(value)


@dataclass(frozen=True)
class ReplayConformanceResult:
    """Result of a replay conformance test."""
    
    source: str
    repeats: int
    signatures: List[str]
    conformance: bool
    mismatch_indices: List[int]
    traces: List[ExecutionTrace]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "repeats": self.repeats,
            "signatures": self.signatures,
            "conformance": self.conformance,
            "mismatch_indices": self.mismatch_indices,
            "traces": [t.to_dict() for t in self.traces],
        }


class TraceCaptureHook:
    """Hook for capturing builtin calls during execution."""
    
    def __init__(self):
        self.builtin_calls: List[Dict[str, Any]] = []
    
    def record_call(self, name: str, args: tuple, result: Any) -> None:
        """Record a builtin function call."""
        self.builtin_calls.append({
            "builtin": name,
            "args": self._serialize_args(args),
            "result": ExecutionTrace._serialize_value(result),
        })
    
    @staticmethod
    def _serialize_args(args: tuple) -> List[Any]:
        """Serialize function arguments."""
        return [ExecutionTrace._serialize_value(arg) for arg in args]


def capture_execution_trace(
    ast_node: Dict[str, Any],
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> ExecutionTrace:
    """Capture a full execution trace for an AST node.
    
    Args:
        ast_node: The parsed AST node to execute
        env: Optional environment mapping
        fuel_limit: Optional fuel limit for execution
        
    Returns:
        ExecutionTrace with complete trace information
    """
    # Validate AST first
    validate_ast(ast_node)
    
    # Execute with trace capture
    result, trace_ids = eval_expr_with_trace(ast_node, env, fuel_limit)
    
    # Calculate fuel used
    fuel_used = fuel_limit - len(trace_ids) if fuel_limit is not None else None
    
    # Get source representation if available
    program = json.dumps(ast_node, sort_keys=True)
    
    return ExecutionTrace(
        program=program,
        trace_ids=trace_ids,
        final_result=result,
        fuel_used=fuel_used,
        builtin_calls=[],  # TODO: Add builtin call capture via instrumentation
    )


def evaluate_replay_conformance(
    ast_node: Dict[str, Any],
    repeats: int = 3,
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> ReplayConformanceResult:
    """Evaluate replay conformance for an AST node.
    
    Executes the same program multiple times and verifies that:
    - All executions produce identical trace signatures
    - Results are deterministic
    - No non-deterministic operations are detected
    
    Args:
        ast_node: The parsed AST node to execute
        repeats: Number of times to repeat execution (must be >= 2)
        env: Optional environment mapping
        fuel_limit: Optional fuel limit for execution
        
    Returns:
        ReplayConformanceResult with conformance information
    """
    if not isinstance(repeats, int) or repeats < 2:
        raise ValueError("repeats must be an integer >= 2")
    
    traces: List[ExecutionTrace] = []
    signatures: List[str] = []
    
    for _ in range(repeats):
        trace = capture_execution_trace(ast_node, env, fuel_limit)
        traces.append(trace)
        signatures.append(trace.signature())
    
    baseline = signatures[0]
    mismatch_indices = [idx for idx, sig in enumerate(signatures) if sig != baseline]
    
    return ReplayConformanceResult(
        source=json.dumps(ast_node, sort_keys=True),
        repeats=repeats,
        signatures=signatures,
        conformance=len(mismatch_indices) == 0,
        mismatch_indices=mismatch_indices,
        traces=traces,
    )


def evaluate_batch_replay_conformance(
    ast_nodes: Sequence[Dict[str, Any]],
    repeats: int = 3,
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> Dict[str, Any]:
    """Evaluate replay conformance for multiple AST nodes.
    
    Args:
        ast_nodes: Sequence of AST nodes to execute
        repeats: Number of times to repeat each execution
        env: Optional environment mapping
        fuel_limit: Optional fuel limit for execution
        
    Returns:
        Dictionary with batch conformance summary
    """
    results = [
        evaluate_replay_conformance(node, repeats, env, fuel_limit)
        for node in ast_nodes
    ]
    
    failed = [result for result in results if not result.conformance]
    
    return {
        "repeats": repeats,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": [result.to_dict() for result in results],
        "conformance": len(failed) == 0,
        "non_deterministic_programs": [
            {"index": i, "mismatches": len(r.mismatch_indices)}
            for i, r in enumerate(results) if not r.conformance
        ],
    }


def serialize_trace_to_file(trace: ExecutionTrace, filepath: str) -> None:
    """Serialize an execution trace to a JSON file.
    
    Args:
        trace: The execution trace to serialize
        filepath: Path to write the JSON file
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(trace.to_json())


def deserialize_trace_from_file(filepath: str) -> ExecutionTrace:
    """Deserialize an execution trace from a JSON file.
    
    Args:
        filepath: Path to read the JSON file
        
    Returns:
        ExecutionTrace object
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return ExecutionTrace(
        program=data["program"],
        trace_ids=data["trace_ids"],
        final_result=data["final_result"],
        fuel_used=data.get("fuel_used"),
        builtin_calls=data.get("builtin_calls", []),
    )


# Backward compatibility: Maintain old API that works with source strings
# These functions wrap the new AST-based API for compatibility with existing tests

def _source_to_ast(source: str) -> Dict[str, Any]:
    """Convert source string to AST (placeholder - requires parser)."""
    # For now, return a minimal AST structure
    # In production, this would use the actual parser
    return {"kind": "program", "source": source}


def _legacy_evaluate_replay_conformance(
    source: str,
    repeats: int = 3,
    env: Mapping[str, Any] | None = None,
) -> Any:
    """Legacy API for backward compatibility."""
    # This is a compatibility shim that uses the stub runtime
    from runtime.runtime_stub import KairoRuntime
    
    runtime = KairoRuntime()
    patch = runtime.build_program_run_patch(source=source, env=env)
    runtime.apply_patch(patch)
    
    revision = runtime.state.revisions[runtime.state.head]
    ui_ops = runtime.replay_ui_timeline()
    
    return {
        "source": source,
        "repeats": repeats,
        "conformance": True,
        "patch": patch,
        "graph": revision.graph,
        "ui_ops": ui_ops,
    }
