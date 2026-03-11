#!/usr/bin/env python3
"""KAIRO CLI - Unified tool for LNC validation, execution, and replay testing.

Commands:
  validate    Validate LNC files for syntax and schema compliance
  execute     Execute an LNC contract with optional trace capture
  replay-test Run replay conformance tests on LNC contracts

Usage:
  kairo_cli.py validate [PATH]
  kairo_cli.py execute <LNC_FILE> [--env KEY=VALUE] [--fuel LIMIT]
  kairo_cli.py replay-test <LNC_FILE> [--repeats N] [--fuel LIMIT]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.runtime_stub_parts import KairoRuntime
from runtime.replay_conformance import evaluate_replay_conformance
from runtime.replay_harness import ConformanceHarness

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_EXECUTION_ERROR = 2
EXIT_REPLAY_MISMATCH = 3


# Import LNC validator logic
VALID_TASK_STATUS = {"open", "in_progress", "done", "cancelled"}
VALID_PRIORITY = {"p0", "p1", "p2", "p3"}
REQUIRED_FIELDS = {
    "task": {"lnc_version", "kind", "id", "title", "status"},
    "decision": {"lnc_version", "kind", "id", "topic", "decision"},
    "note": {"lnc_version", "kind", "id"},
    "code_unit": {"lnc_version", "kind", "id", "module", "entry"},
}


def _parse_yaml_simple(content: str) -> tuple:
    """Simple YAML parser for LNC files."""
    result = {}
    errors = []
    current_list = None
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        stripped = line.lstrip()
        
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        
        if '\t' in line[:len(line) - len(stripped)]:
            errors.append((line_num, "TAB character in indentation"))
        
        indent = len(line) - len(stripped)
        
        if stripped.startswith('- '):
            if current_list is not None:
                item = stripped[2:].strip()
                if ': ' in item and not item.startswith('"'):
                    key, val = item.split(': ', 1)
                    current_list.append({key.strip(): val.strip()})
                else:
                    current_list.append(item)
        elif ': ' in stripped or stripped.endswith(':'):
            current_list = None
            if ': ' in stripped:
                key, val = stripped.split(': ', 1)
                key = key.rstrip(':').strip()
                val = val.strip()
                
                if val in ['|', '>']:
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
                    items = val[1:-1].split(',')
                    result[key] = [item.strip() for item in items]
                else:
                    result[key] = val
            else:
                key = stripped.rstrip(':').strip()
                result[key] = []
                current_list = result[key]
        
        i += 1
    
    return result, errors


def _validate_file(path: str, seen_ids: set) -> tuple:
    """Validate a single LNC file."""
    errors = []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return False, [f"LNC_READ_001: Cannot read file: {e}"]
    
    if not lines:
        return False, ["LNC_PARSE_001: empty file"]
    
    first_line = lines[0].strip()
    if not first_line.startswith("@lnc "):
        return False, ["LNC_PARSE_001: missing '@lnc <version>' header"]
    
    yaml_content = '\n'.join(lines[1:])
    parsed, yaml_errors = _parse_yaml_simple(yaml_content)
    
    for line_num, msg in yaml_errors:
        errors.append(f"LNC_YAML_{line_num:03d}: {msg}")
    
    kind = parsed.get('kind', 'unknown')
    if kind not in REQUIRED_FIELDS:
        errors.append(f"LNC_KIND_001: unknown kind '{kind}'")
        return False, errors
    
    required = REQUIRED_FIELDS[kind]
    missing = required - set(parsed.keys())
    for field in missing:
        errors.append(f"LNC_VAL_001: missing required field '{field}' for kind '{kind}'")
    
    item_id = parsed.get('id')
    if item_id:
        if item_id in seen_ids:
            errors.append(f"LNC_VAL_004: duplicate id '{item_id}'")
        seen_ids.add(item_id)
    
    if kind == 'task':
        status = parsed.get('status', '').lower()
        if status and status not in VALID_TASK_STATUS:
            errors.append(f"LNC_VAL_002: invalid status '{status}'")
        
        priority = parsed.get('priority', '').lower()
        if priority and priority not in VALID_PRIORITY:
            errors.append(f"LNC_VAL_003: invalid priority '{priority}'")
    
    return len(errors) == 0, errors


def _iter_lnc_files(path: str) -> List[str]:
    """Iterate over all .lnc files in path."""
    if os.path.isfile(path):
        return [path]
    
    files = []
    for root, _dirs, filenames in os.walk(path):
        for name in sorted(filenames):
            if name.endswith(".lnc"):
                files.append(os.path.join(root, name))
    return files


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate LNC files."""
    target = args.path or "/home/node/.openclaw/workspace/llm-native-lang/runtime"
    
    targets = _iter_lnc_files(target)
    if not targets:
        print("No .lnc files found.")
        return EXIT_SUCCESS
    
    seen_ids: set = set()
    failures = []
    
    for path in targets:
        ok, messages = _validate_file(path, seen_ids)
        if not ok:
            for msg in messages:
                failures.append((path, msg))
    
    if failures:
        print("Validation failed:")
        for path, message in failures:
            print(f"  FAIL {path}: {message}")
        return EXIT_VALIDATION_FAILURE
    
    print(f"PASS validated {len(targets)} .lnc file(s)")
    return EXIT_SUCCESS


def cmd_execute(args: argparse.Namespace) -> int:
    """Execute an LNC contract."""
    lnc_file = args.lnc_file
    
    if not os.path.exists(lnc_file):
        print(f"ERROR: File not found: {lnc_file}")
        return EXIT_EXECUTION_ERROR
    
    try:
        with open(lnc_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Cannot read file: {e}")
        return EXIT_EXECUTION_ERROR
    
    # Parse env vars
    env = {}
    if args.env:
        for env_str in args.env:
            if '=' in env_str:
                key, val = env_str.split('=', 1)
                env[key] = val
    
    # Parse fuel limit
    fuel_limit = args.fuel if args.fuel else None
    
    # Execute using runtime stub
    runtime = KairoRuntime()
    
    try:
        patch = runtime.build_program_run_patch(source=content, env=env)
        runtime.apply_patch(patch)
        
        revision = runtime.state.revisions[runtime.state.head]
        
        print(f"Executed: {lnc_file}")
        print(f"Patch ID: {patch['patch_id']}")
        print(f"Head: {runtime.state.head}")
        print(f"Revisions: {len(runtime.state.revisions)}")
        
        if args.trace:
            # Capture trace using conformance harness
            harness = ConformanceHarness(output_dir=args.trace_dir or "./traces")
            trace = harness.capture_and_save(
                lambda: runtime.build_program_run_patch(source=content, env=env),
                f"exec_{Path(lnc_file).stem}",
                []
            )
            print(f"Trace saved: {harness.output_dir}/{trace.trace_id}.json")
        
        return EXIT_SUCCESS
        
    except Exception as e:
        print(f"Execution failed: {e}")
        return EXIT_EXECUTION_ERROR


def cmd_replay_test(args: argparse.Namespace) -> int:
    """Run replay conformance tests."""
    lnc_file = args.lnc_file
    repeats = args.repeats or 3
    
    if not os.path.exists(lnc_file):
        print(f"ERROR: File not found: {lnc_file}")
        return EXIT_EXECUTION_ERROR
    
    try:
        with open(lnc_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Cannot read file: {e}")
        return EXIT_EXECUTION_ERROR
    
    print(f"Running replay conformance test on: {lnc_file}")
    print(f"Repeats: {repeats}")
    
    harness = ConformanceHarness(output_dir=args.trace_dir or "./traces")
    
    def run_contract():
        runtime = KairoRuntime()
        patch = runtime.build_program_run_patch(source=content, env={})
        runtime.apply_patch(patch)
        return runtime.state.head
    
    result = harness.run_conformance_test(
        run_contract,
        f"replay_{Path(lnc_file).stem}",
        iterations=repeats
    )
    
    print(f"\nResults:")
    print(f"  Trace IDs: {result['traces']}")
    print(f"  All match: {result['all_match']}")
    
    if result['violations']:
        print(f"  Violations: {result['violations']}")
        return EXIT_REPLAY_MISMATCH
    else:
        print("  No violations - PASS")
        return EXIT_SUCCESS


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KAIRO CLI - LNC validation, execution, and replay testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kairo_cli.py validate                    # Validate all runtime/examples
  kairo_cli.py validate path/to/file.lnc   # Validate single file
  kairo_cli.py execute examples/task.lnc   # Execute contract
  kairo_cli.py replay-test examples/task.lnc --repeats 5
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate LNC files for syntax and schema compliance"
    )
    validate_parser.add_argument(
        "path",
        nargs="?",
        help="File or directory to validate (default: runtime/examples)"
    )
    
    # execute command
    execute_parser = subparsers.add_parser(
        "execute",
        help="Execute an LNC contract"
    )
    execute_parser.add_argument(
        "lnc_file",
        help="Path to LNC file to execute"
    )
    execute_parser.add_argument(
        "--env",
        action="append",
        help="Environment variables (KEY=VALUE)"
    )
    execute_parser.add_argument(
        "--fuel",
        type=int,
        help="Fuel limit for execution"
    )
    execute_parser.add_argument(
        "--trace",
        action="store_true",
        help="Capture execution trace"
    )
    execute_parser.add_argument(
        "--trace-dir",
        help="Directory for trace output (default: ./traces)"
    )
    
    # replay-test command
    replay_parser = subparsers.add_parser(
        "replay-test",
        help="Run replay conformance tests"
    )
    replay_parser.add_argument(
        "lnc_file",
        help="Path to LNC file to test"
    )
    replay_parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Number of repetitions (default: 3)"
    )
    replay_parser.add_argument(
        "--fuel",
        type=int,
        help="Fuel limit for execution"
    )
    replay_parser.add_argument(
        "--trace-dir",
        help="Directory for trace output"
    )
    
    args = parser.parse_args()
    
    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "execute":
        return cmd_execute(args)
    elif args.command == "replay-test":
        return cmd_replay_test(args)
    else:
        parser.print_help()
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
