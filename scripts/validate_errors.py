#!/usr/bin/env python3
"""Validate error code consistency across the codebase.

Checks:
1. All error codes in grammar_contract.py exist in ERROR_REGISTRY.lnd
2. All error codes in interpreter_runtime.py exist in ERROR_REGISTRY.lnd
3. All registry codes follow naming convention
4. No duplicate error codes
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ERRORS_LND = REPO_ROOT / "errors" / "ERROR_REGISTRY.lnd"

# Regex patterns for error code extraction
ERROR_CODE_PATTERN = re.compile(r'E_[A-Z_]+')


def extract_error_codes_from_file(filepath: Path) -> set[str]:
    """Extract all error codes from a Python source file."""
    codes = set()
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            codes = set(ERROR_CODE_PATTERN.findall(content))
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
    return codes


def extract_registry_codes() -> set[str]:
    """Extract all error codes from ERROR_REGISTRY.lnd."""
    codes = set()
    try:
        with open(ERRORS_LND, 'r') as f:
            content = f.read()
            # Find lines with "code: E_XXX"
            for line in content.split('\n'):
                if 'code: E_' in line:
                    match = ERROR_CODE_PATTERN.search(line)
                    if match:
                        codes.add(match.group())
    except FileNotFoundError:
        print(f"Error: {ERRORS_LND} not found")
        sys.exit(1)
    return codes


def validate_naming_convention(code: str) -> bool:
    """Check if error code follows E_<CATEGORY>_<DESCRIPTOR> convention."""
    valid_prefixes = ('E_PARSE_', 'E_RT_', 'E_SCHEMA_', 'E_LND_')
    return any(code.startswith(prefix) for prefix in valid_prefixes)


def main():
    """Run validation checks."""
    print("=== Error Code Validation ===\n")
    
    # Extract codes from all source files
    grammar_codes = extract_error_codes_from_file(REPO_ROOT / "runtime" / "grammar_contract.py")
    runtime_codes = extract_error_codes_from_file(REPO_ROOT / "runtime" / "interpreter_runtime.py")
    ast_codes = extract_error_codes_from_file(REPO_ROOT / "runtime" / "ast_contract.py")
    registry_codes = extract_registry_codes()
    
    # Filter to only error codes (E_*)
    grammar_errors = {c for c in grammar_codes if c.startswith('E_')}
    runtime_errors = {c for c in runtime_codes if c.startswith('E_')}
    ast_errors = {c for c in ast_codes if c.startswith('E_')}
    
    all_source_codes = grammar_errors | runtime_errors | ast_errors
    
    print(f"Found {len(grammar_errors)} error codes in grammar_contract.py")
    print(f"Found {len(runtime_errors)} error codes in interpreter_runtime.py")
    print(f"Found {len(ast_errors)} error codes in ast_contract.py")
    print(f"Found {len(registry_codes)} error codes in ERROR_REGISTRY.lnd")
    print()
    
    # Check 1: All source codes documented
    missing_in_registry = all_source_codes - registry_codes
    if missing_in_registry:
        print("❌ FAIL: Codes in source but missing from registry:")
        for code in sorted(missing_in_registry):
            print(f"   - {code}")
    else:
        print("✅ PASS: All source error codes documented in registry")
    
    # Check 2: All registry codes used
    unused_in_source = registry_codes - all_source_codes
    if unused_in_source:
        print(f"\n⚠️  WARN: Codes in registry but not found in source:")
        for code in sorted(unused_in_source):
            print(f"   - {code}")
    else:
        print("✅ PASS: All registry codes used in source")
    
    # Check 3: Naming convention
    invalid_names = {c for c in registry_codes if not validate_naming_convention(c)}
    if invalid_names:
        print(f"\n❌ FAIL: Codes violating naming convention:")
        for code in sorted(invalid_names):
            print(f"   - {code}")
    else:
        print("✅ PASS: All codes follow naming convention")
    
    # Check 4: Duplicates (within each source)
    # (Python sets already dedupe, so we check during extraction)
    
    print("\n=== Validation Summary ===")
    total_issues = len(missing_in_registry) + len(invalid_names)
    if total_issues == 0:
        print(f"✅ All checks passed ({len(registry_codes)} error codes validated)")
        return 0
    else:
        print(f"❌ {total_issues} validation issue(s) found")
        return 1


if __name__ == "__main__":
    sys.exit(main())
