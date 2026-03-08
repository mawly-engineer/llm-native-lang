#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def split_cycle_log(text: str):
    lines = text.splitlines()
    idx = lines.index("entries:")
    return lines[: idx + 1], lines[idx + 1 :]


def extract_blocks(body_lines: list[str]) -> list[list[str]]:
    blocks = []
    cur = None
    for ln in body_lines:
        if ln.startswith("  - cycle_id:"):
            if cur is not None:
                blocks.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur is not None:
        blocks.append(cur)
    return blocks


def parse_cycle_id(first_line: str) -> int:
    m = re.match(r"\s*- cycle_id: (\d+)", first_line)
    return int(m.group(1)) if m else -1


def compact(path: Path, max_entries: int) -> str:
    text = path.read_text(encoding="utf-8")
    header, body = split_cycle_log(text)
    blocks = extract_blocks(body)
    if len(blocks) <= max_entries:
        return "CYCLE_LOG: no compaction needed"

    removed = blocks[:-max_entries]
    kept = blocks[-max_entries:]
    fr = parse_cycle_id(removed[0][0])
    lr = parse_cycle_id(removed[-1][0])
    fk = parse_cycle_id(kept[0][0])
    lk = parse_cycle_id(kept[-1][0])

    out = header + [""]
    out.append("  # compacted by scripts/cycle_log_maintain.py")
    out.append(f"  # removed_entries: {len(removed)}")
    out.append(f"  # removed_cycle_range: {fr}-{lr}")
    out.append(f"  # kept_cycle_range: {fk}-{lk}")
    out.append("")
    for b in kept:
        out.extend(b)
        out.append("")

    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return f"CYCLE_LOG: compacted removed={len(removed)} range={fr}-{lr} kept={len(kept)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/node/.openclaw/workspace/llm-native-lang")
    ap.add_argument("--max-entries", type=int, default=20)
    args = ap.parse_args()

    repo = Path(args.repo)
    cycle_log = repo / "evolution" / "CYCLE_LOG.lnd"
    print(compact(cycle_log, args.max_entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
