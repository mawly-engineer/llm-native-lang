#!/usr/bin/env python3
"""Generate changelog from cycle logs."""

import re
from pathlib import Path
from datetime import datetime


def parse_cycle_log():
    """Parse cycle log entries and extract meaningful changes."""
    cycle_log_path = Path(__file__).parent.parent / "evolution" / "CYCLE_LOG.lnd"
    content = cycle_log_path.read_text()
    
    entries = []
    current_entry = None
    
    for line in content.split("\n"):
        line = line.strip()
        
        if line.startswith("- cycle:"):
            current_entry = {"cycle": int(line.split(":")[1].strip())}
        elif line.startswith("timestamp_utc:") and current_entry:
            current_entry["timestamp"] = line.split(":", 1)[1].strip()
        elif line.startswith("type:") and current_entry:
            current_entry["type"] = line.split(":")[1].strip()
        elif line.startswith("implementation_delta:") and current_entry:
            delta = line.split(":", 1)[1].strip().strip('"')
            current_entry["delta"] = delta
        elif line == "" and current_entry:
            if "delta" in current_entry:
                entries.append(current_entry)
            current_entry = None
    
    return entries


def main():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    cycle_log_path = Path(__file__).parent.parent / "evolution" / "CYCLE_LOG.lnd"
    
    # Get current version
    version = "0.0.0"
    match = re.search(r'version = "([^"]+)"', pyproject_path.read_text())
    if match:
        version = match.group(1)
    
    # Get last 5 cycles
    entries = parse_cycle_log()
    recent = entries[-5:] if len(entries) > 5 else entries
    
    print(f"## Release v{version}")
    print(f"\n**Release Date:** {datetime.utcnow().strftime('%Y-%m-%d')}")
    print(f"\n### Recent Changes\n")
    
    for entry in reversed(recent):
        delta = entry.get("delta", "")
        # Extract first sentence or truncate
        desc = delta.split(".")[0] if "." in delta else delta[:100]
        if len(desc) > 100:
            desc = desc[:97] + "..."
        print(f"- {desc}")
    
    print(f"\n### Full Changelog")
    print(f"\nSee [CYCLE_LOG.lnd](evolution/CYCLE_LOG.lnd) for complete history.")


if __name__ == "__main__":
    main()