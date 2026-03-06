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
- `replay_ui_timeline(head)` rekonstruiert den gewünschten UI-Stand aus der Event-Kette
- `rollback_ui(revision)` verschiebt nur den Head; Historie bleibt unverändert erhalten
- `ui_patch` kann als reguläre Op in `apply_patch` enthalten sein (auch mehrfach pro Patch) und schreibt atomar mit Graph-Änderungen
- Jede Program-Revision trägt die gekoppelte `ui_revision` des resultierenden UI-Heads
- Bei UI-Base-Mismatch schlägt der gesamte Program-Patch fehl (keine Teilanwendung)
