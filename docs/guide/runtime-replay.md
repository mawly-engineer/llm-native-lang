# Runtime Replay System

The Runtime Replay system enables deterministic execution capture and validation for LLM-Native Contracts.

## Overview

Runtime Replay provides:

- **Trace Capture** - Record execution traces with full state
- **Deterministic Replay** - Re-run executions with identical results
- **Conformance Testing** - Validate that replays match originals
- **Non-determinism Detection** - Identify non-deterministic operations

## Core Components

### TraceCapture

Records execution state at each step:

```python
from llm_native_lang.runtime.replay_harness import TraceCapture

capture = TraceCapture()
capture.record_step(
    operation="contract_execution",
    inputs={"contract_id": "TASK-001"},
    outputs={"status": "completed"},
    timestamp=time.time()
)
```

### ExecutionTrace

Immutable record of execution:

```python
from llm_native_lang.runtime.replay_harness import ExecutionTrace

trace = ExecutionTrace(
    trace_id="trace-001",
    start_time=time.time(),
    end_time=time.time() + 1.0,
    operations=[...],
    final_state={"status": "done"}
)

# Serialize to JSON
json_data = trace.to_json()
```

### ReplayValidator

Compare original and replayed traces:

```python
from llm_native_lang.runtime.replay_harness import ReplayValidator

validator = ReplayValidator()
result = validator.compare_traces(original_trace, replayed_trace)

if result.matches:
    print("✓ Replay matches original")
else:
    print(f"✗ Mismatches: {result.differences}")
```

### ConformanceHarness

Full conformance testing:

```python
from llm_native_lang.runtime.replay_harness import ConformanceHarness

def my_workflow():
    # Your code here
    return result

harness = ConformanceHarness()
report = harness.run_conformance_test(my_workflow, iterations=3)

print(f"Success rate: {report.success_rate}")
print(f"Average duration: {report.avg_duration_ms}ms")
```

## Example: Contract Execution with Trace Capture

```python
import time
from llm_native_lang.runtime.replay_harness import (
    TraceCapture, ExecutionTrace, ReplayValidator
)
from llm_native_lang.runtime.lnc_contract_loader import LNCContractLoader

# Load a contract
loader = LNCContractLoader("runtime/examples/sample.lnc")
contract = loader.load()

# Execute with trace capture
capture = TraceCapture()
capture.record_step(
    operation="contract_load",
    inputs={"path": "runtime/examples/sample.lnc"},
    outputs={"contract_id": contract.id},
    timestamp=time.time()
)

# Execute contract logic
start_time = time.time()
result = execute_contract(contract)
end_time = time.time()

# Record execution
trace = capture.finalize_trace(
    trace_id="exec-001",
    start_time=start_time,
    end_time=end_time,
    final_state=result
)

# Replay and validate
replayed_result = execute_contract(contract)
replayed_trace = capture.finalize_trace(...)

validator = ReplayValidator()
validation = validator.compare_traces(trace, replayed_trace)

assert validation.matches, "Execution must be deterministic"
```

## Detecting Non-determinism

The replay system automatically detects:

- Time-dependent operations
- Random number generation
- File system interactions
- Network calls
- External dependencies

## Best Practices

1. **Capture at appropriate granularity** - Not too fine, not too coarse
2. **Include relevant state** - Inputs, outputs, and key intermediates
3. **Use timestamps for ordering** - Not for deterministic validation
4. **Test multiple iterations** - At least 3 to catch non-determinism
5. **Log mismatches** - Understand why replays differ

## Integration with LNC Contracts

When executing LNC contracts:

```python
from llm_native_lang.runtime.replay_harness import ConformanceHarness
from llm_native_lang.runtime.lnc_contract_loader import LNCContractLoader

loader = LNCContractLoader()
contract = loader.load("task.lnc")

harness = ConformanceHarness()
report = harness.run_conformance_test(
    lambda: execute_contract(contract),
    iterations=3
)

if report.all_match:
    print(f"✓ Contract execution is deterministic")
    print(f"  Duration: {report.avg_duration_ms:.2f}ms")
else:
    print(f"✗ Non-deterministic execution detected")
```

## API Reference

See the [Runtime API](../api/runtime.md) for complete documentation.
