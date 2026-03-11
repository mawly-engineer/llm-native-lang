# Architecture

## Overview

LLM-Native Lang is a language-native development ecosystem with the following architecture:

## Core Components

### 1. LND Format (LLM-Native Declaration)

- **Purpose**: Structured declarations for LLM consumption
- **Format**: YAML with `@lnd 0.2` header
- **Use Cases**: Agent profiles, run configurations, state tracking
- **Location**: `evolution/`

### 2. LNC Format (LLM-Native Contract)

- **Purpose**: Executable contracts for tasks and decisions
- **Format**: YAML with `@lnc 0.2` header
- **Use Cases**: Task tracking, decision records, code units
- **Location**: `runtime/examples/`, `contracts/`

### 3. Runtime Replay System

- **Purpose**: Deterministic execution capture and validation
- **Components**:
  - `TraceCapture` - Record execution steps
  - `ExecutionTrace` - Immutable execution record
  - `ReplayValidator` - Compare traces
  - `ConformanceHarness` - Run conformance tests

### 4. Validation System

- **LND Validator**: `src/llm_native_lang/validators/lnd_validate.py`
- **LNC Validator**: `src/llm_native_lang/validators/lnc_validate.py`
- **Incremental Validator**: `validate_incremental.py`

### 5. CLI Tools

- **kairo**: Unified CLI (`src/llm_native_lang/cli/kairo_cli.py`)
- **lnd-validate**: LND validation
- **lnc-validate**: LNC validation

## Data Flow

```
LND/LNC Files → Validators → Runtime → Trace Capture → Replay Validation
     ↓              ↓           ↓            ↓              ↓
  Profiles    Validation   Execution   Recording     Conformance
```

## Package Structure

```
src/llm_native_lang/
├── __init__.py
├── runtime/
│   ├── __init__.py
│   ├── replay_harness.py       # Replay system
│   └── lnc_contract_loader.py  # Contract loading
├── validators/
│   ├── __init__.py
│   ├── lnd_validate.py         # LND validation
│   └── lnc_validate.py         # LNC validation
└── cli/
    ├── __init__.py
    └── kairo_cli.py            # CLI implementation
```

## Extension Points

1. **New LND kinds**: Add to `LNDValidator.VALID_KINDS`
2. **New LNC kinds**: Add to `LNCValidator.VALID_KINDS`
3. **Custom validators**: Inherit from base validators
4. **Runtime hooks**: Extend `TraceCapture`

## Design Principles

1. **Deterministic**: Reproducible execution
2. **Validated**: Fail fast on invalid input
3. **Composed**: Small, focused components
4. **Observable**: Full trace capture
5. **Testable**: Conformance validation
