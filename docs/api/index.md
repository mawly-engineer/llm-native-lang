# API Reference

This section provides detailed API documentation for the llm-native-lang Python package.

## Package Structure

```
llm_native_lang/
├── __init__.py           # Package metadata
├── runtime/             # Runtime execution
│   ├── replay_harness.py    # Replay and conformance
│   └── lnc_contract_loader.py # Contract loading
├── validators/          # Format validation
│   ├── lnd_validate.py     # LND validator
│   └── lnc_validate.py     # LNC validator
└── cli/                 # Command-line interface
    └── kairo_cli.py        # Main CLI
```

## Installation

```bash
pip install llm-native-lang
```

## Version

```python
from llm_native_lang import __version__

print(__version__)  # e.g., "0.2.0"
```

## Submodules

### Runtime

Execution and replay functionality:

```python
from llm_native_lang.runtime.replay_harness import (
    TraceCapture,
    ExecutionTrace,
    ReplayValidator,
    ConformanceHarness
)
```

### Validators

LND and LNC format validation:

```python
from llm_native_lang.validators.lnd_validate import LNDValidator
from llm_native_lang.validators.lnc_validate import validate_file
```

### CLI

Programmatic CLI access:

```python
from llm_native_lang.cli.kairo_cli import main
```

## Error Handling

All modules use standard Python exceptions:

```python
try:
    result = validate_file("file.lnc")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Validation error: {e}")
```
