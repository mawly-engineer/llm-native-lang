# Runtime API

## TraceCapture

```python
class TraceCapture:
    """Records execution traces with state capture."""
    
    def record_step(
        self,
        operation: str,
        inputs: dict,
        outputs: dict,
        timestamp: float
    ) -> None
        """Record a single execution step."""
    
    def finalize_trace(
        self,
        trace_id: str,
        start_time: float,
        end_time: float,
        final_state: dict
    ) -> ExecutionTrace
        """Finalize and return the execution trace."""
```

## ExecutionTrace

```python
@dataclass
class ExecutionTrace:
    """Immutable record of execution."""
    
    trace_id: str
    start_time: float
    end_time: float
    operations: list[TraceOperation]
    final_state: dict
    
    def to_json(self) -> str
        """Serialize trace to JSON."""
    
    @classmethod
    def from_json(cls, json_str: str) -> ExecutionTrace
        """Deserialize trace from JSON."""
```

## ReplayValidator

```python
class ReplayValidator:
    """Validates replay conformance."""
    
    def compare_traces(
        self,
        original: ExecutionTrace,
        replayed: ExecutionTrace
    ) -> ValidationResult
        """Compare two traces and return validation result."""
```

## ConformanceHarness

```python
class ConformanceHarness:
    """Runs conformance tests across multiple iterations."""
    
    def run_conformance_test(
        self,
        func: Callable,
        iterations: int = 3,
        args: tuple = (),
        kwargs: dict = None
    ) -> ConformanceReport
        """Run conformance test for a function."""

@dataclass
class ConformanceReport:
    """Results from conformance testing."""
    
    iterations: int
    success_count: int
    failure_count: int
    avg_duration_ms: float
    traces: list[ExecutionTrace]
    all_match: bool
    success_rate: float
```

## LNCContractLoader

```python
class LNCContractLoader:
    """Loads and validates LNC contract files."""
    
    def load(self, path: str) -> LNCContract
        """Load and parse an LNC contract file."""
    
    def validate(self, contract: LNCContract) -> tuple[bool, list[str]]
        """Validate a loaded contract."""
```

## Usage Example

```python
from llm_native_lang.runtime.replay_harness import (
    TraceCapture,
    ConformanceHarness
)

# Capture execution
capture = TraceCapture()
capture.record_step(
    operation="my_op",
    inputs={"x": 42},
    outputs={"y": 84},
    timestamp=time.time()
)

# Run conformance test
harness = ConformanceHarness()
report = harness.run_conformance_test(
    my_function,
    iterations=3
)

print(f"Success rate: {report.success_rate}")
```
