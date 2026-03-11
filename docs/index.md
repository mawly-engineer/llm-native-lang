# LLM-Native Language

A **language-native development ecosystem** for LLM-native declarations and contracts.

## What is LLM-Native Lang?

LLM-Native Lang (LNL) provides structured formats for AI-native development:

- **LND Format** - LLM-Native Declarations for agent profiles, protocols, and state
- **LNC Format** - LLM-Native Contracts for task execution and decision tracking
- **Runtime Replay** - Deterministic execution capture and validation
- **CLI Tools** - Unified command-line interface for validation and execution

## Key Features

- 🎯 **Structured Declarations** - YAML-based formats designed for LLM consumption
- 🔁 **Deterministic Replay** - Capture and replay execution traces for validation
- ✅ **Format Validation** - Built-in validators for LND and LNC files
- 🐍 **Python Native** - First-class Python package with CLI tools
- 📦 **Pip Installable** - Standard Python packaging for easy distribution

## Quick Start

### Installation

```bash
pip install llm-native-lang
```

### Validate LND Files

```bash
lnd-validate evolution/
```

### Validate LNC Contracts

```bash
lnc-validate runtime/examples/
```

### Use the KAIRO CLI

```bash
kairo validate evolution/
kairo execute runtime/examples/sample.lnc
```

## Python API

```python
from llm_native_lang import __version__
from llm_native_lang.validators.lnd_validate import LNDValidator
from llm_native_lang.validators.lnc_validate import validate_file

# Validate LND files
validator = LNDValidator()
validator.validate_file("path/to/file.lnd")

# Validate LNC files
ok, errors = validate_file("path/to/file.lnc")
```

## Project Structure

```
llm-native-lang/
├── evolution/          # Agent profiles, runs, protocols
├── formats/            # LND and LNC format specifications
├── runtime/            # Python runtime implementation
├── contracts/          # LNC contract examples
└── scripts/            # Utility scripts and CLI
```

## Next Steps

- [Installation](getting-started/installation.md) - Complete installation guide
- [LND Format Guide](guide/lnd-format.md) - Learn the declaration format
- [LNC Format Guide](guide/lnc-format.md) - Learn the contract format
- [Runtime Replay](guide/runtime-replay.md) - Understand deterministic execution
