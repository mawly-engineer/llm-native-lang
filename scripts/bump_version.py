#!/usr/bin/env python3
"""Bump version in pyproject.toml."""

import re
import sys
from pathlib import Path


def bump_version(current: str, bump_type: str) -> str:
    """Bump semantic version."""
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def main():
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <patch|minor|major>", file=sys.stderr)
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ("patch", "minor", "major"):
        print(f"Invalid bump type: {bump_type}", file=sys.stderr)
        sys.exit(1)
    
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_path.read_text()
    
    # Extract current version
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print("Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    
    current_version = match.group(1)
    new_version = bump_version(current_version, bump_type)
    
    # Replace version
    new_content = re.sub(
        r'(version = )"[^"]+"',
        f'\\1"{new_version}"',
        content
    )
    
    pyproject_path.write_text(new_content)
    print(f"Bumped version: {current_version} -> {new_version}")


if __name__ == "__main__":
    main()