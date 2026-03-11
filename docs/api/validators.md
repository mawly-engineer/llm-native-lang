# Validators API

## LNDValidator

```python
class LNDValidator:
    """Validates LND format files."""
    
    def __init__(self, verbose: bool = False)
        """Initialize validator."""
    
    def validate_file(self, path: str) -> tuple[bool, list[str]]
        """Validate a single LND file.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
    
    def validate_directory(self, path: str) -> dict[str, tuple[bool, list[str]]]
        """Validate all .lnd files in a directory.
        
        Returns:
            Dict mapping file paths to (is_valid, errors) tuples.
        """
    
    def check_id_uniqueness(self, files: list[str]) -> dict[str, list[str]]
        """Check for duplicate IDs across files.
        
        Returns:
            Dict mapping duplicate IDs to lists of files containing them.
        """
```

## LNC Validation

```python
def validate_file(
    path: str,
    verbose: bool = False
) -> tuple[bool, list[str]]
    """Validate a single LNC file.
    
    Args:
        path: Path to LNC file
        verbose: Print detailed output
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """

def validate_directory(
    path: str,
    verbose: bool = False
) -> dict[str, tuple[bool, list[str]]]
    """Validate all .lnc files in a directory.
    
    Args:
        path: Path to directory
        verbose: Print detailed output
    
    Returns:
        Dict mapping file paths to (is_valid, errors) tuples.
    """

def check_lnc_id_uniqueness(
    files: list[str]
) -> dict[str, list[str]]
    """Check for duplicate LNC IDs across files.
    
    Returns:
        Dict mapping duplicate IDs to lists of files containing them.
    """
```

## Validation Rules

### LND Rules

1. Version header must be first line (`@lnd 0.2`)
2. Required fields: `kind`, `id`, `status`
3. Valid YAML syntax
4. No tabs (spaces only)
5. IDs must be unique across all files

### LNC Rules

1. Version header must be first line (`@lnc 0.2`)
2. Required fields: `kind`, `id`, `status`
3. Task status values: `open`, `in_progress`, `done`, `cancelled`
4. Task priority values: `p0`, `p1`, `p2`, `p3`
5. Decision options must have at least 2 items
6. Decision `selected` must match an option ID
7. Valid YAML syntax
8. No tabs (spaces only)
9. IDs must be unique across all files

## Usage Examples

### LND Validation

```python
from llm_native_lang.validators.lnd_validate import LNDValidator

validator = LNDValidator(verbose=True)

# Single file
is_valid, errors = validator.validate_file("agent.lnd")
if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Directory
results = validator.validate_directory("evolution/")
for path, (valid, errs) in results.items():
    status = "✓" if valid else "✗"
    print(f"{status} {path}")
```

### LNC Validation

```python
from llm_native_lang.validators.lnc_validate import (
    validate_file,
    validate_directory
)

# Single file
is_valid, errors = validate_file("contract.lnc", verbose=True)

# Directory
results = validate_directory("runtime/examples/")
for path, (valid, errs) in results.items():
    print(f"{'✓' if valid else '✗'} {path}")
```

## CLI Commands

### lnd-validate

```bash
# Single file
lnd-validate agent.lnd

# Directory
lnd-validate evolution/

# With verbose output
lnd-validate -v evolution/
```

### lnc-validate

```bash
# Single file
lnc-validate contract.lnc

# Directory
lnc-validate runtime/examples/

# With verbose output
lnc-validate -v runtime/examples/
```
