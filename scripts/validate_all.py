#!/usr/bin/env python3
"""Unified validator - runs all checks in single Python process."""
import subprocess
import sys
import os

REPO_ROOT = "/home/node/.openclaw/workspace/llm-native-lang"

def run_validators(changed_domains=None):
    """Run validators intelligently based on what changed."""
    results = []
    
    # Runtime tests (slowest - only if runtime/ changed)
    if not changed_domains or "runtime" in changed_domains:
        results.append((
            "runtime_tests",
            subprocess.run([
                sys.executable, "-m", "unittest", "discover", "-s", "runtime", "-p", "test_*.py", "-v"
            ], cwd=REPO_ROOT, capture_output=True, text=True)
        ))
    
    # LND validation (fast - always run for safety)
    for domain in ["evolution", "contracts", "formats"]:
        if not changed_domains or domain in changed_domains:
            results.append((
                f"lnd_{domain}",
                subprocess.run(
                    [sys.executable, "scripts/lnd_validate.py", domain],
                    cwd=REPO_ROOT, capture_output=True, text=True
                )
            ))
    
    # LNC validation (fast)
    if not changed_domains or "runtime" in changed_domains:
        results.append((
            "lnc_runtime",
            subprocess.run(
                [sys.executable, "scripts/lnc_validate.py", "runtime"],
                cwd=REPO_ROOT, capture_output=True, text=True
            )
        ))
    
    # Report results
    all_passed = True
    for name, result in results:
        status = "PASS" if result.returncode == 0 else "FAIL"
        if result.returncode != 0:
            all_passed = False
            print(f"[{status}] {name}:")
            print(result.stderr[-500:] if result.stderr else result.stdout[-500:])
        else:
            print(f"[{status}] {name}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed", help="Comma-separated list of changed domains")
    args = parser.parse_args()
    
    changed = args.changed.split(",") if args.changed else None
    sys.exit(run_validators(changed))
