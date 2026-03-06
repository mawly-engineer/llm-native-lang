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
