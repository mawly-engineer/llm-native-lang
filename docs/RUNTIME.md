# KAIRO Runtime v0.1

## Pipeline
1. Input (User/LLM/Event/File)
2. Normalize → Internal Event
3. Resolve Module Graph Dependencies
4. Execute in Sandbox
5. Emit State Deltas
6. Compile UI Patches
7. Apply Incremental Updates to Interaction Space
8. Persist Revision + Audit Trail

## Runtime-Komponenten
- **Event Bus**: priorisierte Ereignisse, idempotente Verarbeitung
- **Graph Scheduler**: topologische Ausführung von Modulabhängigkeiten
- **Semantic Store**: Graph + Embeddings + Kontextfenster
- **Patch Engine**: strukturelle Änderungen an Program + UI + State
- **UI Sync Engine**: delta-basiertes Live-Update
- **Policy VM**: Policy Evaluation + Enforcement
- **Revision Manager**: Snapshot + Diff + Rollback + Branch

## Ausführungsgrenzen (Safety)
- CPU/Memory/IO Budgets pro Job
- syscall-/connector-allowlist
- timeouts + cancellation tokens
- read-only fallback mode bei Policy-Verstößen

## Fehlermodell
- Recoverable Error: Retry / Degrade
- Policy Error: Hard deny + audit event
- Integrity Error: Rollback auf letzte konsistente Revision

## UI Event-Sourcing Skizze (Cycle 011/012)
- UI-Änderungen werden als append-only Timeline gespeichert (`u-0`, `u-1`, ...)
- Jede UI-Revision referenziert ihren Parent (Head-basierte Fortschreibung)
- `apply_ui_patch` normalisiert Ops vor Persistenz (deterministisch + konfliktreduziert)
- `replay_ui_timeline(head)` rekonstruiert den gewünschten UI-Stand DAG-nativ über `parent` + `secondary_parent`
- `create_ui_snapshot(head)` speichert einen kompaktisierten UI-Stand (`s-*`) für einen Timeline-Head
- Replay kann bei vorhandenen Snapshots vom nächsten (distanzbasierten) Snapshot-Vorfahren starten, auch wenn dieser über den sekundären Merge-Parent erreichbar ist
- `replay_ui_timeline(..., include_metrics=True)` exponiert Replay-Kosten (`events_replayed`, `snapshot_seed_distance`) als Runtime-Metriken; `events_replayed` zählt dabei den effektiven Replay-Pfad (auch bei delta-base-seeded Merge-Replays)
- `rollback_ui(revision)` verschiebt nur den Head; Historie bleibt unverändert erhalten
- `ui_patch` kann als reguläre Op in `apply_patch` enthalten sein (auch mehrfach pro Patch) und schreibt atomar mit Graph-Änderungen
- Jede Program-Revision trägt die gekoppelte `ui_revision` des resultierenden UI-Heads
- Bei UI-Base-Mismatch schlägt der gesamte Program-Patch fehl (keine Teilanwendung)
- UI-Branch-Merge via `preview_ui_merge(...)` / `merge_ui_branches(...)`:
  - Base wird optional per LCA bestimmt
  - Policy v0.1 = `explicit_conflict` (kein stilles Overwrite bei konkurrierenden Writes)
  - optionale manuelle Auflösung pro Op-Key via `resolutions[]` (`accept_left|accept_right`)
  - Merge-Events tragen explizite Dual-Parents (`parent`, `secondary_parent`) plus optionales `resolution_notes`-Decision-Log
- `preview_ui_merge_delta(...)` ermöglicht einen nicht-destruktiven Vergleich zwischen materialisiertem Merge-Stand (`merged_ops`) und einem Delta-Set (`delta_ops`) relativ zur Base, inkl. Rekonstruktionsinvariante als Vorbereitung für mögliche Delta-Persistenz.

## Replay-Metrik Troubleshooting (Cycle 024)
- `events_replayed` misst den effektiven Replay-Pfad nach Snapshot-Seeding; bei Merge-Heads können trotz Snapshot weiterhin mehrere Branch-Events gezählt werden.
- Bei `mode="delta"` wird die Delta-Base zuerst rekonstruiert, danach das Delta-Event angewendet; damit kann `events_replayed` höher ausfallen als `len(delta_ops)`.
- `snapshot_seed_distance` ist die Distanz vom Replay-Head zum gewählten Snapshot-Vorfahren, nicht zur Delta-Base.
- Für Performance-Debugging beide Werte zusammen lesen:
  - hoher `snapshot_seed_distance` + hohe `events_replayed` → zusätzlicher Snapshot nahe am Merge-Head sinnvoll
  - niedriger `snapshot_seed_distance`, aber hohe `events_replayed` → Kosten kommen primär aus Branch-Replay/DAG-Fan-in
