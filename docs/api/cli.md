# CLI API

## kairo

The unified command-line interface for LLM-Native Lang.

### Commands

```bash
kairo [COMMAND] [OPTIONS]
```

#### validate

Validate LND or LNC files:

```bash
# Validate LND files
kairo validate evolution/

# Validate LNC files
kairo validate runtime/examples/

# Specific file
kairo validate agent.lnd

# With verbose output
kairo validate -v evolution/
```

#### execute

Execute an LNC contract:

```bash
# Execute a contract
kairo execute task.lnc

# Execute with trace capture
kairo execute task.lnc --capture

# Execute with specific output
kairo execute task.lnc --output results.json
```

#### replay-test

Run replay conformance test:

```bash
# Test with 3 iterations (default)
kairo replay-test task.lnc

# Test with custom iterations
kairo replay-test task.lnc --iterations 5
```

### Global Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `-q, --quiet` | Suppress non-error output |
| `--version` | Show version and exit |
| `-h, --help` | Show help message |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation failure |
| 2 | Execution error |
| 3 | Invalid arguments |
| 4 | File not found |

## lnd-validate

Dedicated LND file validator.

```bash
lnd-validate [OPTIONS] PATH
```

### Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show detailed output |
| `--check-ids` | Check ID uniqueness across files |
| `-h, --help` | Show help |

### Examples

```bash
# Validate single file
lnd-validate agent.lnd

# Validate directory
lnd-validate evolution/

# Check for duplicate IDs
lnd-validate --check-ids evolution/
```

## lnc-validate

Dedicated LNC file validator.

```bash
lnc-validate [OPTIONS] PATH
```

### Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show detailed output |
| `--check-ids` | Check ID uniqueness across files |
| `-h, --help` | Show help |

### Examples

```bash
# Validate single file
lnc-validate contract.lnc

# Validate directory
lnc-validate runtime/examples/

# Verbose output
lnc-validate -v runtime/examples/
```

## Programmatic Access

Access CLI functionality from Python:

```python
from llm_native_lang.cli.kairo_cli import main
import sys

# Simulate CLI call
sys.argv = ["kairo", "validate", "evolution/"]
main()

# Or use directly
from llm_native_lang.validators.lnd_validate import LNDValidator
from llm_native_lang.validators.lnc_validate import validate_file

# LND validation
validator = LNDValidator()
is_valid, errors = validator.validate_file("agent.lnd")

# LNC validation
is_valid, errors = validate_file("contract.lnc")
```
