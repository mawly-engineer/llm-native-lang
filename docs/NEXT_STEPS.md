# Next Steps

## Cycle 006
- UI Diff Protocol (deterministische Reihenfolge, conflict-safe)
- Event-Sourcing Modell für State + UI Timeline
- Rollback-Strategie mit Testfällen validieren

## Cycle 007
- Query DSL um Operatoren erweitern (`!=`, Prefix/Contains)
- Query-Operatoren mit Unit-Tests absichern
- Type-System-Doku auf neuen Query-Stand bringen

## Cycle 008
- Fehlercodes in eigenes Runtime-Contract-Dokument extrahieren ✅
- Sortierungs-/Limit-Semantik für Query API definieren ✅
- UI Diff Protocol (deterministische Reihenfolge, conflict-safe) vorbereiten

## Cycle 009
- UI Diff Protocol v0.1 als separates Dokument konkretisieren ✅
- Deterministische Op-Reihenfolge + Konfliktregeln definieren ✅
- Erste Golden-Tests für Diff-Reihenfolge im Runtime-Stub skizzieren ✅

## Cycle 010
- Parent/Child-Konflikte im UI Diff behandeln (`/a` vs `/a/b`) ✅
- Event-Sourcing-Skizze (append-only UI Timeline) dokumentieren ✅
- Rollback-Replay-Testfälle im Runtime-Stub vorbereiten ✅

## Cycle 011
- UI Timeline als append-only Runtime-API implementieren ✅
- Replay über frei wählbaren UI-Head ermöglichen ✅
- Rollback-Verhalten mit Tests absichern ✅

## Cycle 012
- `ui_patch` als reguläre Patch-Op in `apply_patch` integrieren ✅
- Program-Revision und UI-Revision transaktional koppeln ✅
- Fehler-/Rollback-Semantik für gemischte Graph+UI-Patches definieren ✅

## Cycle 013
- Mehrere `ui_patch` Ops pro Patch unterstützen ✅
- Validierung für sequenzielle UI-Head-Fortschreibung pro Program-Patch ergänzen ✅
- Tests für mehrstufige UI-Patch-Ketten im selben Commit ergänzen ✅

## Cycle 014
- `ui_patch`-Konfliktmodell für Branch/Merge skizzieren
- Replay-Performance mit Event-Compaction/Snapshot-Idee vorbereiten
- Contract-/Runtime-Doku um Multi-`ui_patch`-Semantik präzisieren

## Cycle 015
- UI-Snapshot-API für Event-Compaction im Runtime-Stub ergänzen ✅
- Replay-Logik snapshot-aware machen (Vorfahren-Snapshot + Rest-Events) ✅
- Snapshot-Verhalten mit Unit-Tests und Runtime-Doku absichern ✅

## Cycle 016
- UI-Branch/Merge-Konfliktmodell für divergente UI-Timelines konkretisieren ✅
- Merge-Policy-Entscheidung dokumentieren (Last-Writer vs explicit conflict) ✅ (`explicit_conflict`)
- Erste Merge-Validierungstests im Runtime-Stub vorbereiten ✅

## Cycle 017
- Merge-Vorschau in echte `merge_ui_branches(...)`-Operation überführen ✅
- Konfliktdetails strukturiert zurückgeben (nicht nur Error-Code) ✅
- Decision-Log für manuelle Konfliktauflösung im Runtime-Contract ergänzen ✅

## Cycle 018
- UI-Merge-Commit mit expliziten Branch-Parents modellieren (statt squash-artigem Materialized Event) ✅
- Merge-Decision-Log als optionalen Input (`resolution_notes`) im Runtime-Contract definieren ✅
- Tests für manuelle Konfliktauflösung (accept-left/right per Op-Key) vorbereiten ✅

## Cycle 019
- Merge-Replay auf echte DAG-Semantik umstellen (nicht nur primären Parent traversieren) ✅
- Snapshot-Index für Merge-Heads (mehrere Vorfahren) erweitern ✅
- Metriken ergänzen: Replay-Kosten vor/nach Merge-Snapshots vergleichen (vorbereitet via DAG-Replay-Basis)

## Cycle 020
- Replay-Metriken als Runtime-API explizit exponieren (`events_replayed`, `snapshot_seed_distance`) ✅
- Delta-basiertes Merge-Event (statt materialisiertem Vollstand) evaluieren
- Contract-Doku um Replay-Kostenmodell für Merge-lastige Timelines ergänzen ✅

## Cycle 021
- Delta-basiertes Merge-Event-Modell als Alternative zu materialisierten Merge-Ops skizzieren ✅
- Vergleich im Contract festhalten: Merge-Replay-Kosten materialisiert vs delta-basiert ✅
- Erste Stub-Tests für Delta-Merge-Invariante vorbereiten (ohne vollständige Persistenzumstellung) ✅

## Cycle 022
- Delta-Merge-Vorschau in echte Merge-Persistenzvariante überführen (`mode=delta|materialized`) ✅
- Replay-Pfad für Delta-Merge-Events auf Korrektheit + Kostenmetrik testen ✅
- Contract um Kompatibilitätsregeln für gemischte Materialized/Delta-Historien ergänzen ✅

## Cycle 023
- Replay-Metrik `events_replayed` für Delta-Merge-Pfade präzisieren (base-seeded statt Postorder-Näherung) ✅
- Merge-Mode-Validierungsfehler in eigenen Fehlercode auslagern (`E_UI_MERGE_MODE`) ✅
- Auto-LCA-Verhalten mit implizitem Root (`None`) in separaten Tests absichern ✅

## Cycle 024
- Delta-Replay-Metriken mit Snapshot-Seed-Kombination absichern ✅
- Merge-API-Fehlercodes zwischen Policy/Mode noch klarer trennen (Doku-Beispiele) ✅
- Replay-Metriken im Runtime-Guide um Troubleshooting-Hinweise ergänzen ✅

## Cycle 025
- Replay-Metrik-Zählweise für Delta+Snapshot bei Merge-Heads gegen tatsächlichen Apply-Pfad validieren ✅
- Optionalen Metrik-Split diskutieren (`events_from_snapshot_seed` vs `events_total`) ✅
- Merge-Replay-Beispiele für größere DAG-Fan-in-Szenarien ergänzen

## Cycle 026
- Metrik-Split in Runtime-API ergänzen (`events_from_snapshot_seed`, `events_total`) ✅
- Bestehende Replay-Metrik-Tests auf den Split ausweiten ✅
- Runtime- und Contract-Doku auf den neuen Metrikvertrag aktualisieren ✅

## Cycle 027
- Merge-Replay-Beispiele für größere DAG-Fan-in-Szenarien ergänzen ✅
- Optionales Szenario für mehrfach verschachtelte Delta-Merges dokumentieren ✅
- Replay-Metriken in einem kompakten Vergleichsbeispiel zusammenfassen ✅

## Cycle 028
- Replay-Metriken für gemischte Merge-Modi (`materialized -> delta`, `delta -> materialized`) systematisch vergleichen ✅
- Runtime-Doku um ein kurzes Entscheidungsraster für die Wahl des Merge-Modus ergänzen ✅
- Optional: Property-basierte Tests für LCA/Base-Validierung in kleinen Zufalls-DAGs vorbereiten

## Cycle 029
- Property-basierte Teststrategie für LCA/Base-Validierung konkretisieren (Generator + Invarianten) ✅
- Erste kleine Zufalls-DAG-Testhülle vorbereiten (noch ohne neue Test-Dependency) ✅
- Contract-Notiz ergänzen, welche Merge-Invarianten dabei hart gelten müssen ✅

## Cycle 030
- Randomisierte Merge-Tests auf explizite Base-Mismatch-Negativfälle erweitern ✅
- Delta-vs-Materialized in Random-Szenarien auf identische Endzustände vergleichen ✅
- Runtime-Doku um kurze Anleitung für reproduzierbare Seed-Debugs ergänzen ✅

## Cycle 031
- Random-Testhülle um gezielte Remove/Insert-UI-Op-Mischungen erweitern
- Merge-Resolver-Strategien (`accept_left` vs `accept_right`) im Seed-Vergleich gegeneinander profilieren
- Contract-Beispiel ergänzen: reproduzierbarer Bugreport mit Seed + minimalem Merge-Case

