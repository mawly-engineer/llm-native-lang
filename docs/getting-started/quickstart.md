# Quickstart Guide

This guide will get you up and running with LLM-Native Lang in minutes.

## Validate Your First LND File

Create a file `hello.lnd`:

```yaml
@lnd 0.2
kind: agent_profile
id: hello-world-agent
status: active
purpose: A simple example agent

workspace_root: /home/user/workspace

authoritative_inputs:
  - hello_config.json
```

Validate it:

```bash
lnd-validate hello.lnd
```

Output:
```
✓ hello.lnd: valid
```

## Create Your First LNC Contract

Create a file `task.lnc`:

```yaml
@lnc 0.2
kind: task
id: my-first-task
status: open
priority: p1

objective: |
  Learn how to use LNC contracts for task tracking.

acceptance_criteria:
  - Understand LNC format structure
  - Create a valid contract file
  - Validate using lnc-validate
```

Validate it:

```bash
lnc-validate task.lnc
```

## Execute a Contract

```bash
kairo execute task.lnc
```

This will:
1. Load and validate the contract
2. Execute any actions defined
3. Capture execution trace

## Batch Validation

Validate all LND files in a directory:

```bash
lnd-validate evolution/
```

Validate all LNC files:

```bash
lnc-validate runtime/examples/
```

## Replay Validation

Test that your execution is deterministic:

```python
from llm_native_lang.runtime.replay_harness import ConformanceHarness

harness = ConformanceHarness()
harness.run_conformance_test(my_function, iterations=3)
```

## Next Steps

- [LND Format Guide](../guide/lnd-format.md) - Deep dive into declarations
- [LNC Format Guide](../guide/lnc-format.md) - Learn contract patterns
- [Runtime Replay](../guide/runtime-replay.md) - Understand execution capture
