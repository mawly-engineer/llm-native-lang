#!/usr/bin/env python3
"""Detect which domains changed since last successful cycle."""
import subprocess
import json
import os

REPO_ROOT = "/home/node/.openclaw/workspace/llm-native-lang"
STATE_FILE = os.path.join(REPO_ROOT, "evolution", "LAST_KNOWN_GOOD_COMMIT")

def get_changed_domains():
    """Returns list of changed domains or None if full validation needed."""
    try:
        # Get last known good commit
        if not os.path.exists(STATE_FILE):
            return None  # Full validation on first run
        
        with open(STATE_FILE) as f:
            last_good = f.read().strip()
        
        # Get current HEAD
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        current = result.stdout.strip()
        
        if last_good == current:
            return []  # No changes at all
        
        # Get changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", last_good, current],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        
        changed_files = result.stdout.strip().split("\n")
        domains = set()
        
        for f in changed_files:
            if f.startswith("runtime/"):
                domains.add("runtime")
            elif f.startswith("evolution/"):
                domains.add("evolution")
            elif f.startswith("contracts/"):
                domains.add("contracts")
            elif f.startswith("formats/"):
                domains.add("formats")
        
        return list(domains) if domains else []
        
    except Exception:
        return None  # Fallback to full validation

def mark_good_commit():
    """Mark current commit as known good."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    with open(STATE_FILE, "w") as f:
        f.write(result.stdout.strip())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark", action="store_true", help="Mark current commit as good")
    args = parser.parse_args()
    
    if args.mark:
        mark_good_commit()
        print("Marked current commit as known good")
    else:
        domains = get_changed_domains()
        if domains is None:
            print("FULL")  # Signal to run everything
        elif not domains:
            print("NONE")  # No changes, skip validation
        else:
            print(",".join(domains))
