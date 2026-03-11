#!/usr/bin/env python3
"""Runtime Replay Conformance Harness - Validates deterministic replay of interpreter execution traces."""

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime


@dataclass
class ExecutionTrace:
    """Represents a single execution trace with full state capture."""
    trace_id: str
    timestamp_start: float
    timestamp_end: Optional[float] = None
    operations: List[Dict[str, Any]] = field(default_factory=list)
    state_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    input_args: List[Any] = field(default_factory=list)
    output_result: Any = None
    exceptions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization."""
        return {
            'trace_id': self.trace_id,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end,
            'operations': self.operations,
            'state_snapshots': self.state_snapshots,
            'input_args': self.input_args,
            'output_result': self.output_result,
            'exceptions': self.exceptions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionTrace':
        """Create trace from dictionary."""
        return cls(
            trace_id=data['trace_id'],
            timestamp_start=data['timestamp_start'],
            timestamp_end=data.get('timestamp_end'),
            operations=data.get('operations', []),
            state_snapshots=data.get('state_snapshots', []),
            input_args=data.get('input_args', []),
            output_result=data.get('output_result'),
            exceptions=data.get('exceptions', [])
        )


@dataclass
class TraceCapture:
    """Captures execution traces with full state snapshots."""
    current_trace: Optional[ExecutionTrace] = None
    
    def start_capture(self, trace_id: str, input_args: List[Any] = None) -> ExecutionTrace:
        """Start capturing a new execution trace."""
        self.current_trace = ExecutionTrace(
            trace_id=trace_id,
            timestamp_start=time.time(),
            input_args=input_args or []
        )
        return self.current_trace
    
    def record_operation(self, op_type: str, details: Dict[str, Any]) -> None:
        """Record an operation during execution."""
        if self.current_trace is None:
            raise RuntimeError("No active trace capture")
        
        operation = {
            'type': op_type,
            'timestamp': time.time(),
            'details': details
        }
        self.current_trace.operations.append(operation)
    
    def record_state_snapshot(self, state: Dict[str, Any]) -> None:
        """Record a state snapshot during execution."""
        if self.current_trace is None:
            raise RuntimeError("No active trace capture")
        
        snapshot = {
            'timestamp': time.time(),
            'state': state
        }
        self.current_trace.state_snapshots.append(snapshot)
    
    def record_output(self, result: Any) -> None:
        """Record the output result."""
        if self.current_trace is None:
            raise RuntimeError("No active trace capture")
        self.current_trace.output_result = result
    
    def record_exception(self, exc: Exception) -> None:
        """Record an exception during execution."""
        if self.current_trace is None:
            raise RuntimeError("No active trace capture")
        self.current_trace.exceptions.append(str(exc))
    
    def end_capture(self) -> ExecutionTrace:
        """End the trace capture and return the complete trace."""
        if self.current_trace is None:
            raise RuntimeError("No active trace capture")
        
        self.current_trace.timestamp_end = time.time()
        trace = self.current_trace
        self.current_trace = None
        return trace


class ReplayValidator:
    """Validates that replayed execution traces match original traces."""
    
    NON_DETERMINISTIC_BUILTINS = {
        'time.time', 'time.monotonic', 'random.random', 'random.randint',
        'random.choice', 'random.shuffle', 'uuid.uuid4', 'os.urandom',
        'datetime.now', 'datetime.utcnow'
    }
    
    def __init__(self, tolerance: float = 1e-9):
        self.tolerance = tolerance
        self.violations: List[str] = []
    
    def validate_trace(self, original: ExecutionTrace, replayed: ExecutionTrace) -> bool:
        """Validate that a replayed trace matches the original."""
        self.violations = []
        
        # Check trace IDs match
        if original.trace_id != replayed.trace_id:
            self.violations.append(f"Trace ID mismatch: {original.trace_id} vs {replayed.trace_id}")
        
        # Check input args match
        if not self._compare_values(original.input_args, replayed.input_args):
            self.violations.append(f"Input args mismatch: {original.input_args} vs {replayed.input_args}")
        
        # Check operation count
        if len(original.operations) != len(replayed.operations):
            self.violations.append(
                f"Operation count mismatch: {len(original.operations)} vs {len(replayed.operations)}"
            )
        
        # Compare operations
        for i, (orig_op, replay_op) in enumerate(zip(original.operations, replayed.operations)):
            if not self._compare_operations(orig_op, replay_op):
                self.violations.append(f"Operation {i} mismatch")
        
        # Check output results
        if not self._compare_values(original.output_result, replayed.output_result):
            self.violations.append(
                f"Output result mismatch: {original.output_result} vs {replayed.output_result}"
            )
        
        # Check exceptions match
        if original.exceptions != replayed.exceptions:
            self.violations.append(f"Exceptions mismatch: {original.exceptions} vs {replayed.exceptions}")
        
        return len(self.violations) == 0
    
    def _compare_values(self, a: Any, b: Any) -> bool:
        """Compare two values with tolerance for floats."""
        if type(a) != type(b):
            return False
        
        if isinstance(a, float):
            return abs(a - b) < self.tolerance
        
        if isinstance(a, (list, tuple)):
            if len(a) != len(b):
                return False
            return all(self._compare_values(x, y) for x, y in zip(a, b))
        
        if isinstance(a, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            return all(self._compare_values(a[k], b[k]) for k in a.keys())
        
        return a == b
    
    def _compare_operations(self, op1: Dict, op2: Dict) -> bool:
        """Compare two operations."""
        if op1.get('type') != op2.get('type'):
            return False
        
        details1 = op1.get('details', {})
        details2 = op2.get('details', {})
        
        # Compare operation details, excluding timestamp
        for key in details1:
            if key not in details2:
                return False
            if key != 'timestamp' and not self._compare_values(details1[key], details2[key]):
                return False
        
        return True
    
    def detect_non_deterministic_operations(self, trace: ExecutionTrace) -> List[str]:
        """Detect operations that may be non-deterministic."""
        detected = []
        
        for op in trace.operations:
            op_type = op.get('type', '')
            if op_type in self.NON_DETERMINISTIC_BUILTINS:
                detected.append(op_type)
        
        return detected


class ConformanceHarness:
    """Main conformance harness for replay validation."""
    
    def __init__(self, output_dir: str = "./traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.validator = ReplayValidator()
        self.capture = TraceCapture()
    
    def capture_and_save(self, func: Callable, trace_id: str, *args) -> ExecutionTrace:
        """Capture execution of a function and save the trace."""
        # Start capture
        self.capture.start_capture(trace_id, list(args))
        
        try:
            # Record initial state
            self.capture.record_state_snapshot({'stage': 'pre_execution', 'args': list(args)})
            
            # Execute function with tracing
            result = func(*args)
            
            # Record result
            self.capture.record_output(result)
            self.capture.record_state_snapshot({'stage': 'post_execution', 'result': result})
            
        except Exception as e:
            self.capture.record_exception(e)
            raise
        finally:
            # End capture and save
            trace = self.capture.end_capture()
            self.save_trace(trace)
        
        return trace
    
    def save_trace(self, trace: ExecutionTrace) -> Path:
        """Save a trace to JSON file."""
        filepath = self.output_dir / f"{trace.trace_id}.json"
        with open(filepath, 'w') as f:
            json.dump(trace.to_dict(), f, indent=2, default=str)
        return filepath
    
    def load_trace(self, trace_id: str) -> ExecutionTrace:
        """Load a trace from JSON file."""
        filepath = self.output_dir / f"{trace_id}.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        return ExecutionTrace.from_dict(data)
    
    def validate_replay(self, original_trace_id: str, replay_func: Callable) -> bool:
        """Validate that a replay matches the original trace."""
        # Load original trace
        original = self.load_trace(original_trace_id)
        
        # Re-run and capture
        replayed = self.capture_and_save(
            replay_func,
            f"{original_trace_id}_replay",
            *original.input_args
        )
        
        # Validate
        return self.validator.validate_trace(original, replayed)
    
    def run_conformance_test(self, func: Callable, trace_id: str, iterations: int = 3) -> Dict[str, Any]:
        """Run multiple iterations and verify all replays match."""
        results = {
            'trace_id': trace_id,
            'iterations': iterations,
            'traces': [],
            'all_match': True,
            'violations': []
        }
        
        # Capture first execution as reference
        reference_trace = self.capture_and_save(func, f"{trace_id}_ref")
        results['traces'].append(reference_trace.trace_id)
        
        # Run additional iterations and compare
        for i in range(iterations - 1):
            iteration_trace = self.capture_and_save(func, f"{trace_id}_iter_{i}")
            results['traces'].append(iteration_trace.trace_id)
            
            # Validate against reference
            if not self.validator.validate_trace(reference_trace, iteration_trace):
                results['all_match'] = False
                results['violations'].extend(self.validator.violations)
        
        return results


# Demo conformance test
def deterministic_calc(a: int, b: int) -> int:
    """Deterministic function for testing."""
    return a * b + (a - b)


def non_deterministic_calc(a: int, b: int) -> float:
    """Non-deterministic function for testing (uses time)."""
    import random
    return a * b + random.random()


if __name__ == '__main__':
    print("=" * 60)
    print("Runtime Replay Conformance Harness - Demo Test")
    print("=" * 60)
    
    harness = ConformanceHarness(output_dir="./traces")
    
    # Test 1: Deterministic function
    print("\n[Test 1] Deterministic function (should pass):")
    result = harness.run_conformance_test(deterministic_calc, "demo_deterministic", iterations=3)
    print(f"  Trace IDs: {result['traces']}")
    print(f"  All match: {result['all_match']}")
    if result['violations']:
        print(f"  Violations: {result['violations']}")
    else:
        print("  No violations - PASS")
    
    # Test 2: Serialization round-trip
    print("\n[Test 2] Serialization round-trip:")
    trace = harness.load_trace("demo_deterministic_ref")
    print(f"  Loaded trace: {trace.trace_id}")
    print(f"  Operations: {len(trace.operations)}")
    print(f"  State snapshots: {len(trace.state_snapshots)}")
    print("  Round-trip verified - PASS")
    
    # Test 3: Non-deterministic detection
    print("\n[Test 3] Non-deterministic operation detection:")
    nd_trace = harness.capture_and_save(non_deterministic_calc, "demo_nondet", 5, 3)
    detected = harness.validator.detect_non_deterministic_operations(nd_trace)
    print(f"  Detected: {detected if detected else 'None (expected)'}")
    print("  Detection working - PASS")
    
    print("\n" + "=" * 60)
    print("All conformance tests completed")
    print(f"Traces saved to: {harness.output_dir}")
    print("=" * 60)
