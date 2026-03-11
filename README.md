# LLM-Native Language

A language-native development ecosystem for LLM-native declarations and contracts.

## Installation

```bash
pip install -e .
```

Or for development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Validate LND files
```bash
lnd-validate evolution/
```

### Validate LNC files
```bash
lnc-validate runtime/examples/
```

### Use the KAIRO CLI
```bash
kairo validate evolution/
```

## Package Structure

- `llm_native_lang.runtime` - Runtime execution modules
- `llm_native_lang.validators` - LND and LNC format validators
- `llm_native_lang.cli` - KAIRO command-line interface

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

## License

MIT License