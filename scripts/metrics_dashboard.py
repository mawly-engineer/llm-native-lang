#!/usr/bin/env python3
"""Generate metrics dashboard from CYCLE_LOG."""
import json
import re
from datetime import datetime

LOG_FILE = "/home/node/.openclaw/workspace/llm-native-lang/evolution/CYCLE_LOG.lnd"

def parse_cycle_log():
    with open(LOG_FILE) as f:
        content = f.read()
    
    # Simple parsing for cycle entries
    cycles = []
    for match in re.finditer(r'cycle_id:\s*(\d+).*?timestamp_utc:\s*"([^"]+)".*?status:\s*(\w+)', content, re.DOTALL):
        cycles.append({
            'id': int(match.group(1)),
            'timestamp': match.group(2),
            'status': match.group(3)
        })
    
    return cycles

def generate_report():
    cycles = parse_cycle_log()
    if not cycles:
        print("No cycle data found")
        return
    
    total = len(cycles)
    done = sum(1 for c in cycles if c['status'] == 'done')
    blocked = sum(1 for c in cycles if c['status'] == 'blocked')
    
    print(f"=== KAIRO Metrics Dashboard ===")
    print(f"Total cycles: {total}")
    print(f"Completed: {done} ({done/total*100:.1f}%)")
    print(f"Blocked: {blocked} ({blocked/total*100:.1f}%)")
    print(f"Success rate: {(total-blocked)/total*100:.1f}%")
    print(f"Latest cycle: {cycles[-1]['id']} at {cycles[-1]['timestamp']}")

if __name__ == "__main__":
    generate_report()
