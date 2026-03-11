#!/usr/bin/env python3
"""LNC format validator - checks syntax, required fields, and constraints."""
import argparse
import os
import sys
import re
from typing import Iterable, Tuple, Dict, List, Set
from pathlib import Path

# Error codes
ERROR_INVALID_HEADER = "LNC_PARSE_001"
ERROR_INVALID_YAML = "LNC_PARSE_002"
ERROR_MISSING_REQUIRED_FIELD = "LNC_VAL_001"
ERROR_INVALID_STATUS = "LNC_VAL_002"
ERROR_INVALID_PRIORITY = "LNC_VAL_003"
ERROR_DUPLICATE_ID = "LNC_VAL_004"
ERROR_PROFILE_MISMATCH = "ERR_PROFILE_MISMATCH"

# Valid values
VALID_TASK_STATUS = {"open", "in_progress", "done", "cancelled"}
VALID_PRIORITY = {"p0", "p1", "p2", "p3"}

# Required fields per kind
REQUIRED_FIELDS = {
    "task": {"lnc_version", "kind", "id", "title", "status"},
    "decision": {"lnc_version", "kind", "id", "topic", "decision"},
    "note": {"lnc_version", "kind", "id"},
    "code_unit": {"lnc_version", "kind", "id", "module", "entry"},
}


def _iter_targets(path: str) -> Iterable[str]:
    """Iterate over all .lnc files in path."""
    if os.path.isfile(path):
        yield path
        return

    for root, _dirs, files in os.walk(path):
        for name in sorted(files):
            if name.endswith(".lnc"):
                yield os.path.join(root, name)


def _parse_yaml_simple(content: str) -> Tuple[Dict, List[Tuple[int, str]]]:
    """
    Simple YAML parser for LNC files.
    Returns (parsed_dict, errors) where errors is list of (line_number, error_message).
    """
    result = {}
    errors = []
    current_key = None
    current_list = None
    current_indent = 0
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        stripped = line.lstrip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        
        # Check for tabs (invalid in YAML)
        if '\t' in line[:len(line) - len(stripped)]:
            errors.append((line_num, "TAB character in indentation (use spaces)"))
        
        indent = len(line) - len(stripped)
        
        # List item
        if stripped.startswith('- '):
            if current_list is not None:
                item = stripped[2:].strip()
                # Handle inline key: value in list items
                if ': ' in item and not item.startswith('"'):
                    key, val = item.split(': ', 1)
                    current_list.append({key.strip(): val.strip()})
                else:
                    current_list.append(item)
            else:
                errors.append((line_num, f"List item outside of list context: {stripped}"))
        
        # Key-value pair
        elif ': ' in stripped or stripped.endswith(':'):
            current_list = None
            if ': ' in stripped:
                key, val = stripped.split(': ', 1)
                key = key.rstrip(':').strip()
                val = val.strip()
                
                # Check if this is a multi-line value (folded or literal style)
                if val in ['|', '>']:
                    # Collect indented lines
                    i += 1
                    multiline_val = []
                    while i < len(lines):
                        next_line = lines[i]
                        if not next_line.strip():
                            i += 1
                            continue
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent and next_line.strip():
                            i -= 1
                            break
                        multiline_val.append(next_line[indent:])
                        i += 1
                    result[key] = '\n'.join(multiline_val)
                elif val.startswith('[') and val.endswith(']'):
                    # Inline list
                    items = val[1:-1].split(',')
                    result[key] = [item.strip() for item in items]
                else:
                    result[key] = val
            else:
                # Key with no value - starts a section/list
                key = stripped.rstrip(':').strip()
                current_key = key
                result[key] = []
                current_list = result[key]
        
        i += 1
    
    return result, errors


def _validate_file(path: str, seen_ids: Set[str]) -> Tuple[bool, List[str]]:
    """
    Validate a single LNC file.
    Returns (ok, messages) where messages is list of error strings.
    """
    errors = []
    
    # Read file
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
            lines = content.split('\n')
    except Exception as e:
        return False, [f"LNC_READ_001: Cannot read file: {e}"]
    
    # Check header
    if not lines:
        return False, [f"{ERROR_INVALID_HEADER}: empty file"]
    
    first_line = lines[0].strip()
    
    if not first_line.startswith("@lnc "):
        if first_line.startswith("@lnd "):
            return False, [f"{ERROR_PROFILE_MISMATCH}: file extension/header family mismatch (.lnc vs @lnd)"]
        return False, [f"{ERROR_INVALID_HEADER}: missing '@lnc <version>' header"]
    
    # Parse YAML content (skip header)
    yaml_content = '\n'.join(lines[1:])
    parsed, yaml_errors = _parse_yaml_simple(yaml_content)
    
    # Report YAML syntax errors
    for line_num, msg in yaml_errors:
        errors.append(f"LNC_YAML_{line_num:03d}: {msg}")
    
    # Check required fields per kind
    kind = parsed.get('kind', 'unknown')
    
    if kind not in REQUIRED_FIELDS:
        errors.append(f"LNC_KIND_001: unknown kind '{kind}'")
        return False, errors
    
    required = REQUIRED_FIELDS[kind]
    missing = required - set(parsed.keys())
    if missing:
        for field in missing:
            errors.append(f"{ERROR_MISSING_REQUIRED_FIELD}: missing required field '{field}' for kind '{kind}'")
    
    # Check ID uniqueness
    item_id = parsed.get('id')
    if item_id:
        if item_id in seen_ids:
            errors.append(f"{ERROR_DUPLICATE_ID}: duplicate id '{item_id}'")
        seen_ids.add(item_id)
    else:
        errors.append(f"{ERROR_MISSING_REQUIRED_FIELD}: missing required field 'id'")
    
    # Task-specific validation
    if kind == 'task':
        status = parsed.get('status', '').lower()
        if status and status not in VALID_TASK_STATUS:
            errors.append(f"{ERROR_INVALID_STATUS}: invalid status '{status}' (expected: {VALID_TASK_STATUS})")
        
        priority = parsed.get('priority', '').lower()
        if priority and priority not in VALID_PRIORITY:
            errors.append(f"{ERROR_INVALID_PRIORITY}: invalid priority '{priority}' (expected: {VALID_PRIORITY})")
    
    # Decision-specific validation
    if kind == 'decision':
        options = parsed.get('options', [])
        selected = parsed.get('selected')
        if isinstance(options, list) and len(options) < 2:
            errors.append("LNC_DEC_001: decision should have at least 2 options")
        if selected and isinstance(options, list) and selected not in [str(opt) for opt in options]:
            errors.append(f"LNC_DEC_002: selected '{selected}' not in options list")
    
    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate .lnc files for syntax, required fields, and constraints."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="/home/node/.openclaw/workspace/llm-native-lang/runtime",
        help="File or directory to validate.",
    )
    args = parser.parse_args()

    targets = list(_iter_targets(args.target))
    if not targets:
        print("No .lnc files found.")
        return 0

    seen_ids: Set[str] = set()
    failures = []
    
    for path in targets:
        ok, messages = _validate_file(path, seen_ids)
        if not ok:
            for msg in messages:
                failures.append((path, msg))

    if failures:
        for path, message in failures:
            print(f"FAIL {path}: {message}")
        return 1

    print(f"PASS validated {len(targets)} .lnc file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
