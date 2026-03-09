#!/usr/bin/env python3
"""Dynamic Batching fuer KAIRO."""
import time
import sys

TIME_THRESHOLD = 120
MAX_ITEMS = 3

def run_batch():
    items_processed = 0
    start = time.time()
    
    for i in range(MAX_ITEMS):
        item_start = time.time()
        print(f"[BATCH] Item {i+1}")
        time.sleep(0.5)
        elapsed = time.time() - item_start
        items_processed += 1
        print(f"[BATCH] Done in {elapsed:.1f}s")
        
        if elapsed > TIME_THRESHOLD:
            print(f"[BATCH] Threshold reached")
            break
    
    total = time.time() - start
    print(f"[BATCH] Total: {items_processed} items, {total:.1f}s")
    return items_processed

if __name__ == '__main__':
    run_batch()
