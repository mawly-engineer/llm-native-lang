#!/usr/bin/env python3
"""
Runtime Replay Conformance Harness
Captures and replays interpreter execution traces for determinism verification.
"""

from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone


@dataclass
class ExecutionFrame:
    """Single frame in execution trace."""
    timestamp: float
    operation: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    exception: Optional[str] = None
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "args": self._serialize_value(self.args),
            "kwargs": self._serialize_value(self.kwargs),
            "result": self._serialize_value(self.result),
            "exception": self.exception,
            "state_snapshot": self._serialize_value(self.state_snapshot)
        }
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value to JSON-compatible format."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [ExecutionFrame._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: ExecutionFrame._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, '__dict__'):
            return ExecutionFrame._serialize_value(vars(value))
        else:
            return str(value)


@dataclass
class ExecutionTrace:
    """Complete execution trace with metadata."""
    trace_id: str
    created_at: str
    source_file: Optional[str] = None
    frames: List[ExecutionFrame] = field(default_factory=list)
    final_state: Dict[str, Any] = field(default_factory=dict)
    
    def add_frame(self, frame: ExecutionFrame) -> None:
        self.frames.append(frame)
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "source_file": self.source_file,
            "frames": [f.to_dict() for f in self.frames],
            "final_state": ExecutionFrame._serialize_value(self.final_state)
        }
    
    def save(self, path: Path) -> None:
        """Save trace to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @staticmethod
    def load(path: Path) -> ExecutionTrace:
        """Load trace from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        trace = ExecutionTrace(
            trace_id=data["trace_id"],
            created_at=data["created_at"],
            source_file=data.get("source_file")
        )
        for frame_data in data.get("frames", []):
            frame = ExecutionFrame(
                timestamp=frame_data["timestamp"],
                operation=frame_data["operation"],
                args=frame_data.get("args", []),
                kwargs=frame_data.get("kwargs", {}),
                result=frame_data.get("result"),
                exception=frame_data.get("exception"),
                state_snapshot=frame_data.get("state_snapshot", {})
            )
            trace.frames.append(frame)
        trace.final_state = data.get("final_state", {})
        return trace


class TraceCapture:
    """Captures execution traces with automatic state snapshots."""
    
    NONDETERMINISTIC_BUILTINS = {
        'time.time', 'time.monotonic', 'time.perf_counter',
        'random.random', 'random.randint', 'random.choice',
        'uuid.uuid4', 'uuid.uuid1', 'os.urandom',
        'datetime.now', 'datetime.utcnow'
    }
    
    def __init__(self, source_file: Optional[str] = None):
        self.trace = ExecutionTrace(
            trace_id=self._generate_trace_id(),
            created_at=datetime.now(timezone.utc).isoformat(),
            source_file=source_file
        )
        self._capture_active = False
    
    def _generate_trace_id(self) -> str:
        return hashlib.sha256(
            f"{time.time()}{id(self)}".encode()
        ).hexdigest()[:16]
    
    def capture(self, operation: str, args: tuple = (), 
                kwargs: dict = None, result: Any = None,
                exception: Optional[Exception] = None,
                state: dict = None) -> ExecutionFrame:
        """Capture a single execution frame."""
        frame = ExecutionFrame(
            timestamp=time.time(),
            operation=operation,
            args=list(args),
            kwargs=kwargs or {},
            result=result,
            exception=str(exception) if exception else None,
            state_snapshot=state or {}
        )
        self.trace.add_frame(frame)
        return frame
    
    def is_nondeterministic(self, operation: str) -> bool:
        """Check if operation is known to be non-deterministic."""
        return operation in self.NONDETERMINISTIC_BUILTINS
    
    def finalize(self, final_state: dict = None) -> ExecutionTrace:
        """Finalize trace capture."""
        if final_state:
            self.trace.final_state = final_state
        return self.trace


class ReplayValidator:
    """Validates trace replay produces identical results."""
    
    def __init__(self, tolerance: float = 1e-9):
        self.tolerance = tolerance
        self.differences: List[Dict[str, Any]] = []
    
    def compare_traces(self, original: ExecutionTrace, 
                       replayed: ExecutionTrace) -> bool:
        """Compare two traces for equivalence."""
        self.differences = []
        
        # Compare frame counts
        if len(original.frames) != len(replayed.frames):
            self.differences.append({
                "type": "frame_count_mismatch",
                "original": len(original.frames),
                "replayed": len(replayed.frames)
            })
            return False
        
        # Compare each frame
        for i, (orig, replay) in enumerate(zip(original.frames, replayed.frames)):
            frame_diffs = self._compare_frames(orig, replay, i)
            self.differences.extend(frame_diffs)
        
        # Compare final states
        state_diffs = self._compare_states(
            original.final_state, replayed.final_state, "final_state"
        )
        self.differences.extend(state_diffs)
        
        return len(self.differences) == 0
    
    def _compare_frames(self, orig: ExecutionFrame, replay: ExecutionFrame, 
                        index: int) -> List[dict]:
        """Compare two execution frames."""
        diffs = []
        
        if orig.operation != replay.operation:
            diffs.append({
                "type": "operation_mismatch",
                "frame": index,
                "original": orig.operation,
                "replayed": replay.operation
            })
        
        if orig.result != replay.result:
            diffs.append({
                "type": "result_mismatch",
                "frame": index,
                "original": orig.result,
                "replayed": replay.result
            })
        
        if orig.exception != replay.exception:
            diffs.append({
                "type": "exception_mismatch",
                "frame": index,
                "original": orig.exception,
                "replayed": replay.exception
            })
        
        return diffs
    
    def _compare_states(self, orig: dict, replay: dict, 
                       path: str) -> List[dict]:
        """Compare two state snapshots recursively."""
        diffs = []
        
        all_keys = set(orig.keys()) | set(replay.keys())
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in orig:
                diffs.append({
                    "type": "missing_in_original",
                    "path": current_path,
                    "value": replay[key]
                })
            elif key not in replay:
                diffs.append({
                    "type": "missing_in_replay",
                    "path": current_path,
                    "value": orig[key]
                })
            elif orig[key] != replay[key]:
                diffs.append({
                    "type": "value_mismatch",
                    "path": current_path,
                    "original": orig[key],
                    "replayed": replay[key]
                })
        
        return diffs
    
    def report(self) -> dict:
        """Generate validation report."""
        return {
            "valid": len(self.differences) == 0,
            "differences": self.differences,
            "difference_count": len(self.differences)
        }


class ConformanceHarness:
    """Main entry point for replay conformance testing."""
    
    def __init__(self, output_dir: Path = Path("traces")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.validator = ReplayValidator()
    
    def capture_trace(self, target: Callable, *args, 
                      source_file: str = None, **kwargs) -> Tuple[ExecutionTrace, Any]:
        """Execute target and capture trace."""
        capture = TraceCapture(source_file=source_file)
        result = None
        exception = None
        
        try:
            result = target(*args, **kwargs)
            capture.capture(
                operation=f"call:{target.__name__}",
                args=args,
                kwargs=kwargs,
                result=result
            )
        except Exception as e:
            exception = e
            capture.capture(
                operation=f"call:{target.__name__}",
                args=args,
                kwargs=kwargs,
                exception=e
            )
        
        trace = capture.finalize(final_state={"result": result})
        return trace, result if exception is None else exception
    
    def save_trace(self, trace: ExecutionTrace, name: str = None) -> Path:
        """Save trace to file."""
        filename = f"{name or trace.trace_id}.json"
        path = self.output_dir / filename
        trace.save(path)
        return path
    
    def load_trace(self, path: Path) -> ExecutionTrace:
        """Load trace from file."""
        return ExecutionTrace.load(path)
    
    def verify_roundtrip(self, trace: ExecutionTrace) -> bool:
        """Verify trace serializes and deserializes correctly."""
        path = self.output_dir / "roundtrip_test.json"
        trace.save(path)
        loaded = ExecutionTrace.load(path)
        
        # Compare key attributes
        return (
            trace.trace_id == loaded.trace_id and
            trace.created_at == loaded.created_at and
            len(trace.frames) == len(loaded.frames)
        )
    
    def run_conformance_test(self, target: Callable, *args, 
                             iterations: int = 3, **kwargs) -> dict:
        """Run full conformance test with multiple iterations."""
        results = {
            "target": target.__name__,
            "iterations": iterations,
            "traces": [],
            "comparisons": [],
            "nondeterministic_ops": [],
            "valid": True
        }
        
        traces = []
        for i in range(iterations):
            trace, result = self.capture_trace(target, *args, **kwargs)
            traces.append(trace)
            results["traces"].append({
                "iteration": i,
                "trace_id": trace.trace_id,
                "frame_count": len(trace.frames)
            })
            
            # Check for non-deterministic operations
            for frame in trace.frames:
                if TraceCapture().is_nondeterministic(frame.operation):
                    results["nondeterministic_ops"].append({
                        "iteration": i,
                        "operation": frame.operation
                    })
        
        # Compare all pairs
        for i in range(len(traces)):
            for j in range(i + 1, len(traces)):
                match = self.validator.compare_traces(traces[i], traces[j])
                results["comparisons"].append({
                    "pair": (i, j),
                    "match": match,
                    "differences": self.validator.differences.copy() if not match else []
                })
                if not match:
                    results["valid"] = False
        
        # Verify roundtrip on first trace
        results["roundtrip_valid"] = self.verify_roundtrip(traces[0])
        
        return results


def demo_test():
    """Demo test showing harness functionality."""
    harness = ConformanceHarness()
    
    # Test deterministic function
    def deterministic_calc(x: int, y: int) -> int:
        return (x + y) * 2
    
    print("Running conformance test on deterministic_calc...")
    results = harness.run_conformance_test(deterministic_calc, 5, 3, iterations=3)
    
    print(f"\nResults:")
    print(f"  Target: {results['target']}")
    print(f"  Valid: {results['valid']}")
    print(f"  Roundtrip: {results['roundtrip_valid']}")
    print(f"  Traces captured: {len(results['traces'])}")
    
    if not results['valid']:
        print(f"  Comparisons failed:")
        for comp in results['comparisons']:
            if not comp['match']:
                print(f"    Pair {comp['pair']}: {len(comp['differences'])} differences")
    
    return results


if __name__ == "__main__":
    demo_test()
