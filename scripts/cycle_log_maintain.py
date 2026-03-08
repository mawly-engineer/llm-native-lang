#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def split_cycle_log(text: str):
    lines = text.splitlines()
    try:
        idx = lines.index("entries:")
    except ValueError:
        raise SystemExit("entries: section not found")
    header = lines[: idx + 1]
    body = lines[idx + 1 :]
    return header, body


def extract_entry_blocks(body_lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for ln in body_lines:
        if ln.startswith("  - cycle_id:"):
            if current is not None:
                blocks.append(current)
            current = [ln]
        elif current is not None:
            current.append(ln)
    if current is not None:
        blocks.append(current)
    return blocks


def parse_cycle_id(block: list[str]) -> int | None:
    m = re.match(r"\s*- cycle_id: (\d+)", block[0])
    return int(m.group(1)) if m else None


def compact_cycle_log(path: Path, max_entries: int) -> tuple[int, int, int, int] | None:
    text = path.read_text(encoding="utf-8")
    header, body = split_cycle_log(text)
    blocks = extract_entry_blocks(body)
    if len(blocks) <= max_entries:
        return None

    kept = blocks[-max_entries:]
    removed = blocks[:-max_entries]

    first_removed = parse_cycle_id(removed[0]) or -1
    last_removed = parse_cycle_id(removed[-1]) or -1
    first_kept = parse_cycle_id(kept[0]) or -1
    last_kept = parse_cycle_id(kept[-1]) or -1

    out_lines = header + [""] + ["  # compacted by scripts/cycle_log_maintain.py"]
    out_lines.append(f"  # removed_entries: {len(removed)}")
    out_lines.append(f"  # removed_cycle_range: {first_removed}-{last_removed}")
    out_lines.append(f"  # kept_cycle_range: {first_kept}-{last_kept}")
    out_lines.append("")

    for b in kept:
        out_lines.extend(b)
        out_lines.append("")

    path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    return len(removed), first_removed, last_removed, len(kept)


def extract_done_features(backlog_text: str):
    lines = backlog_text.splitlines()
    out = []
    current_id = None
    current_title = None
    for ln in lines:
        m_id = re.match(r"\s*- id: (.+)", ln)
        if m_id:
            current_id = m_id.group(1).strip()
            current_title = None
            continue
        m_title = re.match(r"\s*title: (.+)", ln)
        if m_title and current_id:
            current_title = m_title.group(1).strip()
            continue
        m_status = re.match(r"\s*status: (.+)", ln)
        if m_status and current_id:
            status = m_status.group(1).strip()
            if status == "done":
                out.append((current_id, current_title or ""))
            current_id = None
            current_title = None
    return out


def write_features_done(path: Path, features: list[tuple[str, str]]):
    lines = [
        "@lnd 0.2",
        "kind: feature_registry",
        "id: LNG-FEATURES-DONE-001",
        "status: active",
        "updated_at_utc: 2026-03-08T01:15:00Z",
        "purpose: Compact registry of implemented backlog features.",
        "",
        "implemented_features:",
    ]
    for fid, title in features:
        lines.append(f"  - id: {fid}")
        lines.append(f"    title: {title}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/node/.openclaw/workspace/llm-native-lang")
    ap.add_argument("--max-entries", type=int, default=120)
    args = ap.parse_args()

    repo = Path(args.repo)
    cycle_log = repo / "evolution" / "CYCLE_LOG.lnd"
    backlog = repo / "evolution" / "LANGUAGE_BACKLOG.lnd"
    features_done = repo / "evolution" / "FEATURES_DONE.lnd"

    result = compact_cycle_log(cycle_log, args.max_entries)
    features = extract_done_features(backlog.read_text(encoding="utf-8"))
    write_features_done(features_done, features)

    if result is None:
        print("CYCLE_LOG: no compaction needed")
    else:
        removed, first_removed, last_removed, kept = result
        print(f"CYCLE_LOG: compacted removed={removed} range={first_removed}-{last_removed} kept={kept}")
    print(f"FEATURES_DONE: wrote {len(features)} implemented features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
