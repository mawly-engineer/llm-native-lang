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
- `replay_ui_timeline(..., include_metrics=True)` exponiert Replay-Kosten (`events_replayed`, `events_from_snapshot_seed`, `events_total`, `snapshot_seed_distance`) als Runtime-Metriken:
  - `events_replayed` (kompatibler Alias) und `events_from_snapshot_seed` zählen den effektiven Replay-Pfad ab Snapshot-Seed
  - `events_total` zählt die gesamte Event-Anzahl des tatsächlich traversierten Apply-Pfads (inkl. Delta-Base-Rekonstruktion)
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

## Fan-in Vergleich: materialized vs verschachteltes delta (Cycle 027)
Ein kompaktes Vergleichsszenario mit identischem Endzustand zeigt die Metrik-Unterschiede klar:
- Setup: Snapshot auf gemeinsamer Base, danach 2-stufiges Fan-in-Merge (erst links/rechts, dann Top/Side)
- Variante A: beide Merges `mode="materialized"`
- Variante B: beide Merges `mode="delta"`

Beobachtung aus den Runtime-Tests:
- `events_from_snapshot_seed` bleibt in beiden Varianten gleich (`6`), weil der gleiche DAG-Pfad ab Snapshot abgearbeitet wird.
- `events_total` unterscheidet sich deutlich:
  - materialized: `7`
  - nested delta: `3`

Interpretation:
- `events_from_snapshot_seed` zeigt den sichtbaren Replay-Aufwand ab Seed.
- `events_total` zeigt den tatsächlichen internen Apply-Aufwand (inkl. Delta-Base-Rekonstruktion) und eignet sich besser für Modusvergleiche bei Merge-heavy Historien.

## Gemischte Merge-Modi im 2-stufigen Fan-in (Cycle 028)
Beim selben Fan-in-Szenario (gleicher Endzustand, Snapshot auf Base) ergeben sich für `events_total`:
- `materialized -> materialized`: `7`
- `materialized -> delta`: `3`
- `delta -> materialized`: `6`
- `delta -> delta`: `3`

Konstante in allen vier Varianten:
- `events_from_snapshot_seed = 6`

Kurzfazit:
- Der **zweite Merge im Delta-Modus** drückt in diesem Szenario `events_total` am stärksten.
- Ein später materialisierter Merge auf Delta-Historie (`delta -> materialized`) liegt kostenmäßig zwischen den Extremen.

## Entscheidungsraster: `materialized` vs `delta`
- **Nimm `materialized`, wenn ...**
  - du Merge-Events direkt als vollständigen Stand inspizieren möchtest
  - Write-Kosten wichtiger sind als Replay-Kosten
  - Debugging/Forensik eher auf Event-Payload statt Rekonstruktion basiert
- **Nimm `delta`, wenn ...**
  - du Merge-heavy DAGs erwartest und Replay-Kosten (`events_total`) senken willst
  - du Base-gebundene Rekonstruktion explizit akzeptierst
  - Snapshot-Strategien bereits etabliert sind
- **Pragmatischer Mix**
  - frühe Merges materialisiert halten, später Fan-in-Merges als Delta persistieren (`materialized -> delta`)
  - Ergebnis regelmäßig mit `replay_ui_timeline(..., include_metrics=True)` verifizieren

## Reproduzierbare Seed-Debugs für Random-Merge-Tests (Cycle 030)
- Random-Tests sind vollständig seed-basiert; jeder Fail ist mit demselben Seed reproduzierbar.
- Vorgehen bei einem Fehlfall:
  1. Seed aus der Fehlermeldung notieren (oder testweise lokal fix setzen).
  2. Nur den betroffenen Test laufen lassen (schneller Feedback-Loop).
  3. Falls nötig, temporär Logging für `preview["conflicts"]`, `resolutions` und `merged_ops` aktivieren.
- Praxisregel für Bugreports:
  - immer Seed + betroffener Testname + erwartetes vs. tatsächliches `merged_ops`-Delta mitschicken.
