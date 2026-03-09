#!/usr/bin/env python3
"""Incremental validation - only changed files."""
import subprocess
import sys
import os

REPO_ROOT = "/home/node/.openclaw/workspace/llm-native-lang"

def get_changed_files():
    """Get files changed since last successful validation."""
    state_file = os.path.join(REPO_ROOT, ".last_validation_hash")
    
    try:
        if os.path.exists(state_file):
            with open(state_file) as f:
                last_hash = f.read().strip()
            result = subprocess.run(
                ["git", "diff", "--name-only", last_hash, "HEAD"],
                cwd=REPO_ROOT, capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        return None
    except Exception:
        return None

def map_files_to_tests(changed_files):
    """Map changed files to specific test modules."""
    tests = set()
    for f in changed_files:
        if "grammar" in f:
            tests.add("runtime.test_grammar_contract")
        if "ast" in f:
            tests.add("runtime.test_ast_contract")
        if "type" in f:
            tests.add("runtime.test_type_contract")
        if "interpreter" in f:
            tests.add("runtime.test_interpreter_runtime")
        if f.endswith(".lnd"):
            tests.add("lnd")
        if f.endswith(".lnc"):
            tests.add("lnc")
    return list(tests)

def run_incremental_validation():
    changed = get_changed_files()
    if changed is None:
        print("[FULL] Running full validation")
        subprocess.run([sys.executable, "scripts/validate_all.py"], cwd=REPO_ROOT)
        return
    
    if not changed:
        print("[SKIP] No changes")
        return
    
    tests = map_files_to_tests(changed)
    print(f"[INCREMENTAL] Changed: {len(changed)} files -> Tests: {tests}")
    
    for test in tests:
        if test == "lnd":
            subprocess.run([sys.executable, "scripts/lnd_validate.py", "evolution"], cwd=REPO_ROOT)
        elif test == "lnc":
            subprocess.run([sys.executable, "scripts/lnc_validate.py", "runtime"], cwd=REPO_ROOT)
        else:
            subprocess.run([sys.executable, "-m", "unittest", test, "-v"], cwd=REPO_ROOT)

if __name__ == "__main__":
    run_incremental_validation()
