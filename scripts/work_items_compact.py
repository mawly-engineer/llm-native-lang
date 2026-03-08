#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime, timezone

REPO = Path('/home/node/.openclaw/workspace/llm-native-lang')
WORK_ITEMS = REPO / 'evolution' / 'WORK_ITEMS.lnd'
ARCHIVE = REPO / 'evolution' / 'WORK_COMPLETED_ARCHIVE.lnd'


def main() -> int:
    lines = WORK_ITEMS.read_text(encoding='utf-8').splitlines()

    out = []
    i = 0
    current_bucket = None
    archived = []

    bucket_re = re.compile(r'^  ([a-zA-Z0-9_-]+):$')
    item_start_re = re.compile(r'^      - id: (.+)$')

    while i < len(lines):
        ln = lines[i]
        m_bucket = bucket_re.match(ln)
        if m_bucket:
            current_bucket = m_bucket.group(1)
            out.append(ln)
            i += 1
            continue

        m_item = item_start_re.match(ln)
        if m_item:
            block = [ln]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if item_start_re.match(nxt) or bucket_re.match(nxt):
                    break
                block.append(nxt)
                i += 1

            status = None
            title = ''
            for b in block:
                ms = re.match(r'^\s*status: (.+)$', b)
                if ms:
                    status = ms.group(1).strip()
                mt = re.match(r'^\s*title: (.+)$', b)
                if mt:
                    title = mt.group(1).strip()
            item_id = m_item.group(1).strip()

            if status == 'done':
                archived.append((item_id, current_bucket or 'unknown', title))
            else:
                out.extend(block)
            continue

        out.append(ln)
        i += 1

    WORK_ITEMS.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')

    # append/update archive file
    existing_ids = set()
    archive_lines = []
    if ARCHIVE.exists():
        archive_lines = ARCHIVE.read_text(encoding='utf-8').splitlines()
        for ln in archive_lines:
            m = re.match(r'^  - id: (.+)$', ln)
            if m:
                existing_ids.add(m.group(1).strip())
    else:
        archive_lines = [
            '@lnd 0.2',
            'kind: completed_archive',
            'id: WORK-COMPLETED-ARCHIVE-001',
            'status: active',
            'updated_at_utc: 2026-03-08T12:35:00Z',
            'purpose: Archive of completed work items removed from WORK_ITEMS to keep context small.',
            '',
            'completed_items:',
        ]

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for item_id, bucket, title in archived:
        if item_id in existing_ids:
            continue
        archive_lines.append(f'  - id: {item_id}')
        archive_lines.append(f'    bucket: {bucket}')
        archive_lines.append(f'    title: {title}')
        archive_lines.append('    status: done')
        archive_lines.append(f'    archived_at_utc: {ts}')

    # refresh timestamp (best-effort)
    archive_lines = [re.sub(r'^updated_at_utc: .+$', f'updated_at_utc: {ts}', ln) for ln in archive_lines]
    ARCHIVE.write_text('\n'.join(archive_lines).rstrip() + '\n', encoding='utf-8')

    print(f'Archived {len(archived)} done items; WORK_ITEMS compacted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
