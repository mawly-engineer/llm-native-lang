# KAIRO Cycle Log

## Cycle 001 — 2026-03-06T15:55:13Z
### Fokus
Grundarchitektur und v0.1 Basisspezifikation erstellt.

### Geliefert
- Programmmodell als Modulgraph
- Primitive Objektklassen definiert
- Datei-zu-SemanticObject Konversion spezifiziert
- Interaction Space (user/llm/shared) festgelegt
- Runtime-Pipeline v0.1 beschrieben
- PatchEnvelope + Op-Typen + Invarianten definiert

### Offene Lücken
- Formale Typregeln (Type System)
- Query-Sprache für semantischen Graph
- UI-Diff-Algorithmus (normalisierte Patchreihenfolge)
- Connector-API für externe Datenquellen
- Deterministische Test-Suite für Patch-Korrektheit

### Nächster Schritt
Cycle 002: Typ- und Constraint-System + minimal ausführbare Runtime-Demo.

## Cycle 002 — 2026-03-06T16:12:38Z
### Fokus
Type/Constraint-Validierung im Runtime-Stub konkretisieren und dokumentieren.

### Geliefert
- `runtime/runtime_stub.py` auf v0.2 erweitert:
  - strukturierte `PatchError` mit Fehlercodes
  - Patch-Basisvalidierung (Pflichtfelder, `target`, `base_revision`, non-empty `ops`)
  - Node-Schema-Checks (`id`, `type`) und Duplicate-ID-Erkennung
  - Edge-Schema-Checks (`from`, `to`, `contract`) und Dangling-Edge-Prüfung
  - Validierung erlaubt Referenzen auf Nodes, die im selben Patch neu angelegt werden
- Neues Dokument `docs/TYPE_SYSTEM.md` erstellt:
  - v0.1 Schema/Constraints für ModuleNode/ModuleEdge
  - vollständige Liste der Runtime-Fehlercodes
  - Scope + Ausbaupfad festgehalten

### Offene Lücken
- Keine formale Typ-Registry (zulässige `type`-Werte sind noch frei)
- Op-Support weiterhin auf `add_node`/`add_edge` begrenzt
- Keine Query DSL Implementierung
- Keine dedizierten Unit-Tests, nur Sanity-Run

### Nächster Schritt
Cycle 003: Query DSL v0.1 als read-only Selektion über `modules`/`edges` + erste Runtime-API dafür.

## Cycle 003 — 2026-03-06T16:31:00Z
### Fokus
Patch-Op-Abdeckung im Runtime-Stub auf zentrale Graph-Mutationen ausweiten + testbar machen.

### Geliefert
- Runtime unterstützt jetzt zusätzlich `replace_node`, `remove_node`, `remove_edge`
- Sequentielle Validierung über simulierten Zwischenzustand:
  - verhindert Duplikate bei Nodes/Edges
  - erkennt fehlende Ziele bei Replace/Remove
  - blockiert Node-Entfernung solange Kanten auf den Node zeigen
  - erlaubt `remove_edge` + `remove_node` im selben Patch in korrekter Reihenfolge
- Apply-Logik für neue Ops ergänzt (inkl. Node-Replace per `id`)
- Erste Unit-Tests für neue Invarianten und Revisionsfortschritt hinzugefügt (3 grüne Tests)

### Offene Lücken
- `set_attr`, `ui_patch`, `state_patch` noch nicht umgesetzt
- Kein 3-way merge / Konfliktauflösung
- Keine Policy-Gates im Stub

### Nächster Schritt
Cycle 004: `set_attr` + minimale Attribut-Schema-Prüfung ergänzen und Edge-/Node-Indexierung für schnellere Validierung vorbereiten.

## Cycle 004 — 2026-03-06T16:45:00Z
### Fokus
`set_attr` als erste gezielte Node-Mutation mit Attribut-Constraints im Runtime-Stub ergänzen.

### Geliefert
- Neue Op `set_attr` in Validierung + Apply implementiert
  - verlangt `{node_id, key, value}`
  - blockiert unbekannte Nodes
  - schützt reservierte Felder (`id`, `type`)
  - validiert Attribut-Key via Pattern (`[A-Za-z_][A-Za-z0-9_.-]*`)
  - erzwingt, dass bestehende `attrs`-Container Objekte sind
- Runtime-Tests erweitert (2 neue Tests):
  - erfolgreicher Attribut-Write auf bestehende Node
  - Reserved-Key-Fehler (`E_ATTR_RESERVED`)
- Type-System-Doku aktualisiert (Scope + Fehlercodes an Runtime-Stand angepasst)

### Offene Lücken
- Noch kein dediziertes Attribut-Typing pro Node-Typ (z. B. erlaubte Keys/Wertetypen)
- Keine Query DSL Implementierung
- Kein Merge-/Konfliktmodell

### Nächster Schritt
Cycle 005: Query DSL v0.1 (read-only) auf `modules`/`edges` einführen und als Runtime-API exponieren.

## Cycle 005 — 2026-03-06T16:56:00Z
### Fokus
Read-only Query DSL v0.1 für Graph-Inspektion im Runtime-Stub einführen.

### Geliefert
- `query(graph, selector)` als Runtime-API ergänzt
- Selektor-Parser für v0.1 implementiert:
  - `modules`
  - `edges`
  - `modules[id=...]`, `modules[type=...]`
  - `edges[from=...]`, `edges[to=...]`, `edges[contract=...]`
- Fehlercodes für Query-Validierung ergänzt:
  - `E_QUERY_SELECTOR` (Syntax/Format)
  - `E_QUERY_KEY` (ungültiger Filter-Key)
  - `E_QUERY_GRAPH` (ungültige Graph-Collection)
- Unit-Tests erweitert (3 neue Tests):
  - Modul-Selektion nach `type`
  - Edge-Selektion nach `from`
  - Fehlerfall bei ungültigem Query-Key

### Offene Lücken
- Keine Attribut-basierten Filter (`attrs.*`) im Selector
- Query nur mit explizitem `graph`-Argument, kein Head-Shortcut
- Noch keine Sortierungs-/Limit-Semantik

### Nächster Schritt
Cycle 006: UI Diff Protocol (deterministisch, conflict-safe) + Event-Sourcing-Skizze vorbereiten.

## Cycle 006 — 2026-03-06T17:18:00Z
### Fokus
Query DSL um Attribut-Selektoren erweitern und Query-API ergonomischer machen.

### Geliefert
- Query-Selektor akzeptiert jetzt auch Attribut-Keys mit Punktnotation
- Neuer Selektor-Pfad für Module-Attribute: `modules[attr.<key>=<value>]`
- Query kann ohne Graph-Argument direkt gegen die aktuelle Head-Revision laufen (`query(selector)`)
- Query-Validierung für falsche Argumentanzahl und ungültigen Graph-Typ ergänzt
- Unit-Tests erweitert (2 neue Tests):
  - Attribut-Selektion (`attr.render.mode`)
  - Head-Default ohne explizites Graph-Argument

### Offene Lücken
- Keine Operatoren wie `!=`, `contains`, Prefix-Match
- Keine Sortierungs-/Limit-Semantik
- Fehlercodes noch nicht in separates Runtime-Contract-Dokument extrahiert

### Nächster Schritt
Cycle 007: Query DSL um Vergleichsoperatoren erweitern und Runtime-Contract-Dokument für Fehlercodes auslagern.

## Cycle 007 — 2026-03-06T17:30:00Z
### Fokus
Query DSL v0.1 um Vergleichsoperatoren erweitern und über Tests absichern.

### Geliefert
- Selector-Syntax auf Operatoren erweitert: `=`, `!=`, `^=` (Prefix), `*=` (Contains)
- Query-Matcher auf stringbasierte Operatorauswertung erweitert
- Unterstützung gilt für Kernfelder (`id`, `type`, `from`, `to`, `contract`) sowie `modules[attr.<key>...]`
- Unit-Tests erweitert (3 neue Tests):
  - Ungleich-Filter (`modules[type!=...]`)
  - Prefix-Filter auf Attributen (`modules[attr.display.name^=...]`)
  - Contains-Filter (`modules[type*=...]`)
- Type-System-Dokumentation auf neuen Query-Funktionsumfang aktualisiert

### Offene Lücken
- Keine Sortierungs-/Limit-Semantik in Query-Ergebnissen
- Fehlercodes noch nicht in separates Runtime-Contract-Dokument extrahiert
- Keine Policy DSL / Approval Gates im Runtime-Stub

### Nächster Schritt
Cycle 008: Runtime-Contract-Dokument für Fehlercodes auslagern und Query um Sortierung/Limit ergänzen.

## Cycle 008 — 2026-03-06T17:45:00Z
### Fokus
Runtime-Contract für Fehlercodes auslagern und Query API um Sortierung/Limit vervollständigen.

### Geliefert
- Neues Runtime-Contract-Dokument erstellt:
  - zentrale Fehlercode-Liste für Patch-, Op-, Attr- und Query-Validierung
  - Query-Signatur + Ausführungsreihenfolge formalisiert
  - Sortierungs- und Limit-Semantik dokumentiert
- Runtime-Stub Query erweitert:
  - optionale Parameter `sort_by`, `descending`, `limit`
  - Sortierung auf Kernfelder sowie `modules[attr.<key>]`
  - neue Validierungsfehler für Sortier-/Limit-Fehleingaben
- Unit-Tests erweitert (3 neue Tests):
  - sortierte + limitierte Modulabfrage
  - absteigende Attribut-Sortierung
  - Fehlerfall bei ungültigem Limit
- Type-System-Dokument entschlackt und auf Runtime-Contract als zentrale Fehlercode-Referenz umgestellt

### Offene Lücken
- UI Diff Protocol weiterhin nur als To-do, noch kein v0.1 Dokument
- Keine Golden-Tests für deterministische Diff-Reihenfolge
- Kein Event-Sourcing-/Rollback-Modell im Runtime-Stub

### Nächster Schritt
Cycle 009: UI Diff Protocol v0.1 mit deterministischer Reihenfolge und Konfliktregeln spezifizieren.

## Cycle 009 — 2026-03-06T17:58:00Z
### Fokus
UI Diff Protocol v0.1 als klaren Normalisierungsvertrag festziehen und erste Golden-Tests im Runtime-Stub verankern.

### Geliefert
- Neues Dokument „UI Diff Protocol v0.1 (Draft)“ erstellt:
  - Op-Format für `remove|replace|move|insert|set_prop`
  - Konfliktregeln (Remove gewinnt, Last-Write-Wins für `set_prop`)
  - deterministische Sortierung (Pfad + Priorität + Prop-Key)
- Runtime-Stub um `normalize_ui_ops(...)` erweitert:
  - Shape-/Kind-/Path-/Key-Validierung mit neuen UI-Fehlercodes
  - Konfliktreduktion + deterministische Reihenfolge implementiert
- Unit-Tests erweitert (2 neue Golden-/Konflikttests):
  - gemischte Ops werden stabil in eine feste Reihenfolge normalisiert
  - wiederholte `set_prop`-Writes auf gleicher Property behalten den letzten Wert
- Runtime-Contract um UI-Diff-Fehlercodes ergänzt

### Offene Lücken
- Parent/Child-Pfadkonflikte sind noch nicht aufgelöst (`remove(/a)` vs `set_prop(/a/b)`)
- UI-Diff ist noch nicht als `ui_patch` in `apply_patch` integriert
- Kein Event-Sourcing-/Rollback-Replay für UI-Operationen

### Nächster Schritt
Cycle 010: Parent/Child-Konfliktregeln + Event-Sourcing-/Rollback-Skizze ergänzen.

## Cycle 010 — 2026-03-06T18:16:00Z
### Fokus
UI-Diff-Konfliktauflösung für Parent/Child-Pfade robust machen und per Tests absichern.

### Geliefert
- `normalize_ui_ops(...)` erweitert:
  - `remove(path)` wirkt jetzt auf gesamten Subtree (`path` + Kindpfade)
  - vorhandene Ops auf Kindpfaden werden bei Parent-Remove entfernt
  - redundante Child-Removes nach Parent-Remove werden ignoriert
- Unit-Tests erweitert (2 neue Tests):
  - Parent-Remove verwirft Child-`set_prop`/`insert`/`replace`
  - Child-Remove nach Parent-Remove bleibt unterdrückt, unabhängige Pfade bleiben erhalten
- UI-Diff-Dokumentation auf Subtree-Konfliktregel aktualisiert

### Offene Lücken
- Kein Event-Sourcing-Modell für UI-Op-Timeline dokumentiert
- Kein Rollback-/Replay-Mechanismus für UI-Patches im Runtime-Stub
- `ui_patch` weiterhin nicht in `apply_patch` integriert

### Nächster Schritt
Cycle 011: Event-Sourcing-Skizze (append-only UI Timeline) + erste Rollback-Replay-Testfälle ergänzen.

## Cycle 011 — 2026-03-06T18:31:00Z
### Fokus
UI-Event-Sourcing im Runtime-Stub konkretisieren (append-only Timeline + Replay/Rollback).

### Geliefert
- Runtime-Stub um UI-Timeline-API erweitert:
  - `apply_ui_patch(ops, base_revision=None)` erzeugt append-only UI-Revisionen (`u-*`)
  - `replay_ui_timeline(head=None)` rekonstruiert den UI-Stand deterministisch über die Event-Kette
  - `rollback_ui(revision)` verschiebt den UI-Head ohne Historie zu löschen
- Fehlercodes für UI-Revisioning ergänzt:
  - Base-Mismatch bei konkurrierenden UI-Schreibvorgängen
  - ungültige/inkonsistente UI-Revisionen beim Replay
- Unit-Tests erweitert (2 neue Tests):
  - Replay aus append-only Events mit Last-Write-Wins
  - Rollback auf ältere UI-Revision verändert den rekonstruierten Head-Stand
- Runtime- und Contract-Doku auf Event-Sourcing-/Fehlercode-Stand aktualisiert

### Offene Lücken
- `ui_patch` ist noch nicht als reguläre Op in `apply_patch` integriert
- Keine transaktionale Kopplung von Program-Revision und UI-Revision
- Kein Merge-/Konfliktmodell für konkurrierende UI-Branches

### Nächster Schritt
Cycle 012: `ui_patch` in den Patch-Pfad integrieren und Program/UI-Revisionen transaktional koppeln.

## Cycle 012 — 2026-03-06T18:41:00Z
### Fokus
`ui_patch` als reguläre Patch-Op in den Program-Patchfluss integrieren und Graph/UI-Revisionskopplung absichern.

### Geliefert
- Runtime-Stub erweitert:
  - neue `Revision.ui_revision` zur Kopplung von Program- und UI-Head
  - `ui_patch`-Validierung im regulären Patchpfad (`validate_patch`) integriert
  - Shape-/Base-Checks für `ui_patch` ergänzt (inkl. Begrenzung auf eine `ui_patch`-Op pro Patch)
  - `apply_patch` kann jetzt `ui_patch` anwenden und die resultierende UI-Revision im Program-Commit persistieren
- Fehler-/Contract-Semantik präzisiert:
  - neue Fehlercodes für `ui_patch`-Shape, Mehrfach-`ui_patch` und ungültige UI-Base-Revision
  - transaktionales Verhalten dokumentiert: bei UI-Fehlern wird der gesamte Patch verworfen
- Unit-Tests erweitert (2 neue Tests):
  - erfolgreicher gemischter Graph+UI-Patch koppelt `r-*` und `u-*`
  - UI-Base-Mismatch verwirft den gesamten Patch ohne Teilanwendung

### Offene Lücken
- Noch keine Unterstützung für mehrere `ui_patch`-Ops pro Patch (bewusst eingeschränkt)
- Kein Branch-/Merge-Modell für divergente UI-Timelines
- Kein Snapshot/Compaction für lange UI-Eventketten

### Nächster Schritt
Cycle 013: Mehrfach-`ui_patch`-Strategie + UI-Branch/Merge-Skizze + Compaction-Ansatz vorbereiten.

## Cycle 013 — 2026-03-06T19:00:00Z
### Fokus
Mehrere `ui_patch`-Ops pro Program-Patch erlauben und sequenzielle UI-Head-Validierung absichern.

### Geliefert
- Runtime-Validierung für `ui_patch` umgestellt:
  - keine Einmal-Beschränkung mehr pro Program-Patch
  - UI-Base-Checks laufen jetzt gegen einen simulierten, pro Op fortgeschriebenen UI-Head
  - simulierte UI-Revisions-IDs folgen derselben Laufzeitlogik (`u-N`) wie beim Apply
- Unit-Tests erweitert (1 neuer Test):
  - erfolgreicher Patch mit zwei `ui_patch`-Ops schreibt `u-0` + `u-1` und koppelt Program-Head auf `u-1`
- Runtime-/Contract-Doku aktualisiert:
  - Multi-`ui_patch`-Semantik dokumentiert
  - veraltete Einmal-Restriktion entfernt

### Offene Lücken
- Kein Branch-/Merge-Modell für divergente UI-Timelines
- Keine Snapshot-/Compaction-Strategie für lange Replay-Ketten
- Keine explizite Regel, ob spätere `ui_patch`-Ops im selben Patch eigene `base_revision` setzen sollten

### Nächster Schritt
Cycle 014: UI-Branch/Merge-Konfliktmodell skizzieren und Compaction/Snapshot-Ansatz konkretisieren.

## Cycle 015 — 2026-03-06T19:16:00Z
### Fokus
UI-Replay für längere Eventketten per Snapshot-Compaction vorbereiten.

### Geliefert
- Runtime-Stub um UI-Snapshot-Modell erweitert:
  - neue Snapshot-Struktur (`s-*`) mit referenziertem Timeline-Head + normalisierten Ops
  - `create_ui_snapshot(head=None)` erzeugt kompaktisierte Replay-Basis
- `replay_ui_timeline(...)` snapshot-aware gemacht:
  - sucht den nächsten Vorfahren-Snapshot auf dem Head-Pfad
  - replayt nur verbleibende Rest-Events bis zum Ziel-Head
- Unit-Tests erweitert (2 neue Tests):
  - Snapshot bildet den aktuellen Head-Stand konsistent ab
  - Replay über Nachfolger-Events bleibt mit vorhandenem Snapshot deterministisch korrekt
- Runtime-Doku auf Snapshot-/Compaction-Semantik aktualisiert

### Offene Lücken
- Kein Branch-/Merge-Modell für divergente UI-Timelines
- Keine Persistenzstrategie für Snapshot-Retention/Cleanup
- Kein Metrik-Hook zur Messung realer Replay-Performance

### Nächster Schritt
Cycle 016: UI-Branch/Merge-Konfliktmodell konkretisieren und erste Merge-Validierungstests vorbereiten.

## Cycle 016 — 2026-03-06T19:28:40Z
### Fokus
UI-Branch/Merge-Konfliktmodell für divergente UI-Timelines spezifizieren und als Runtime-Validierung abbilden.

### Geliefert
- Runtime-Stub um Merge-Validierung erweitert:
  - neue Hilfen für Timeline-Ahnenmenge und LCA-Bestimmung
  - `validate_ui_merge(left_revision, right_revision, base_revision=None, policy="explicit_conflict")`
  - Base-Validierung gegen beide Branches (Fehler bei nicht gemeinsamem Vorfahren)
- Merge-Policy v0.1 festgelegt: `explicit_conflict`
  - Konflikt, wenn beide Branches denselben Op-Key (`op`,`path`,`key`) relativ zur Base unterschiedlich ändern
  - bei Konflikt harter Abbruch statt implizitem Last-Writer-Wins
- Unit-Tests erweitert (2 neue Tests):
  - konfliktfreier Branch-Merge liefert deterministische `merged_ops`
  - konkurrierende Writes auf identischem Key erzeugen `E_UI_MERGE_CONFLICT`
- Runtime-/Contract-Doku auf Merge-Semantik + neue Fehlercodes aktualisiert

### Offene Lücken
- Noch keine echte Merge-Commit-Operation, nur Validierung/Vorschau
- Konfliktdetails werden noch nicht strukturiert an den Caller zurückgegeben
- Kein Entscheidungslog für manuelle Konfliktauflösung

### Nächster Schritt
Cycle 017: Merge-Vorschau in echte `merge_ui_branches(...)`-Operation überführen und Konfliktdetails als strukturiertes Ergebnis ausgeben.

## Cycle 017 — 2026-03-06T19:44:00Z
### Fokus
UI-Branch-Merge von reiner Validierung/Vorschau zu einer echten Runtime-Operation ausbauen.

### Geliefert
- Runtime-Stub um zwei klare Merge-APIs erweitert:
  - `preview_ui_merge(...)` für strukturierte Vorschau mit `conflicts[]`
  - `merge_ui_branches(...)` für konfliktfreien Merge mit neuer `merged_revision`
- `validate_ui_merge(...)` auf Preview-Logik umgestellt:
  - Konflikte lösen weiterhin `E_UI_MERGE_CONFLICT` aus
  - Konfliktdetails werden zusätzlich strukturiert in `PatchError.details` bereitgestellt
- Unit-Tests erweitert (3 neue Tests):
  - strukturierte Konfliktdetails bei `validate_ui_merge(...)`
  - konfliktbehaftete Vorschau via `preview_ui_merge(...)`
  - erfolgreicher `merge_ui_branches(...)` erzeugt neue UI-Head-Revision
- Next-Steps und Runtime-Contract auf Cycle-017-Stand aktualisiert (inkl. Decision-Log-Hinweis für manuelle Auflösung)

### Offene Lücken
- Merge-Persistenz ist aktuell materialisiert/squash-artig und modelliert noch keine expliziten Dual-Parents
- Manuelle Konfliktauflösung ist nur als Decision-Log-Konvention dokumentiert, noch ohne Resolver-API
- Keine Policy für teilautomatische Auflösung (z. B. accept-left/right pro Op-Key)

### Nächster Schritt
Cycle 018: Merge-Commit-Struktur mit expliziten Parents + manuelle Konfliktauflösungs-API vorbereiten.

## Cycle 018 — 2026-03-06T20:00:00Z
### Fokus
UI-Merge von squash-artiger Persistenz auf explizites Merge-Commit-Modell erweitern und manuelle Konfliktauflösung im Stub verankern.

### Geliefert
- Runtime-Stub erweitert:
  - `UITimelineEvent` trägt jetzt `secondary_parent` und optional `resolution_notes`
  - `merge_ui_branches(...)` persistiert explizite Dual-Parents (`parent=left`, `secondary_parent=right`)
- Manuelle Konfliktauflösung implementiert:
  - `preview_ui_merge(...)` / `validate_ui_merge(...)` / `merge_ui_branches(...)` akzeptieren optional `resolutions[]`
  - unterstützte Entscheidungen pro Op-Key: `accept_left`, `accept_right`
  - angewendete Entscheidungen werden als `applied_resolutions[]` zurückgegeben
  - Resolver-Validierung inkl. neuem Fehlercode `E_UI_MERGE_RESOLUTION`
- Unit-Tests erweitert (3 neue Tests):
  - Merge-Event enthält explizite Branch-Parents + `resolution_notes`
  - konfliktbehafteter Merge wird mit `accept_right` erfolgreich aufgelöst
  - ungültige Resolver-Entscheidung wird korrekt abgewiesen
- Runtime-/Contract-Doku auf Cycle-018-Stand aktualisiert (Resolver-Input + Decision-Log + Parent-Modell).

### Offene Lücken
- Replay traversiert weiterhin primär über `parent` und nutzt `secondary_parent` noch nicht für DAG-native Rekonstruktion
- Merge-Event-Payload bleibt materialisiert; kein delta-basiertes Merge-Event
- Keine Performance-Metriken für Merge-lastige Timeline-Replays

### Nächster Schritt
Cycle 019: DAG-natives Replay + Snapshot-Index für Merge-Heads + Replay-Metriken ergänzen.

## Cycle 019 — 2026-03-06T20:11:00Z
### Fokus
UI-Replay auf echte DAG-Semantik umstellen und Snapshot-Nutzung für Merge-Heads robust machen.

### Geliefert
- Runtime-Stub für UI-Replay erweitert:
  - DAG-Parents (`parent`, `secondary_parent`) werden jetzt rekursiv traversiert
  - deterministisches Postorder-Replay mit Zyklus-Erkennung für UI-Graphen
  - LCA-/Ancestor-Helfer auf DAG-Distanzmodell umgestellt
- Snapshot-Seeding verbessert:
  - Snapshot-Auswahl basiert auf nächstem Vorfahren im DAG (distanzbasiert)
  - funktioniert auch, wenn der beste Snapshot nur über `secondary_parent` erreichbar ist
- Unit-Tests erweitert (2 neue Tests):
  - Replay berücksichtigt sekundären Merge-Parent auch ohne materialisierte Merge-Ops
  - Snapshot auf rechter Merge-Seite wird für Merge-Head-Replay korrekt genutzt
- Runtime-/Contract-/Next-Steps-Doku auf DAG-Replay-Stand aktualisiert

### Offene Lücken
- Replay-Kosten werden noch nicht als explizite Runtime-Metriken ausgegeben
- Merge-Events bleiben materialisiert (kein delta-basiertes Eventmodell)
- Keine Retention-/GC-Strategie für Snapshot-Index bei langen Timelines

### Nächster Schritt
Cycle 020: Replay-Metriken API ergänzen + delta-basiertes Merge-Event evaluieren.

## Cycle 020 — 2026-03-06T20:24:00Z
### Fokus
Replay-Kosten als explizite Runtime-Metriken sichtbar machen und den Contract dafür nachziehen.

### Geliefert
- Runtime-Stub erweitert:
  - `replay_ui_timeline(..., include_metrics=True)` liefert jetzt zusätzlich strukturierte Replay-Metriken
  - neue Metriken: `events_replayed` und `snapshot_seed_distance`
  - Rückwärtskompatibilität bleibt erhalten (`include_metrics=False` liefert weiterhin nur `ops`)
- Unit-Tests erweitert (2 neue Tests):
  - Metrik-Ausgabe ohne Snapshot-Seed
  - Metrik-Ausgabe mit Snapshot-Seed inkl. Distanzprüfung
- Runtime-/Contract-Doku aktualisiert:
  - Metrik-Signatur und Rückgabeformat dokumentiert
  - Replay-Kostenmodell für Snapshot-seeded Replays ergänzt

### Offene Lücken
- Merge-Events sind weiterhin materialisierte Vollstände statt Delta-Events
- Keine Metrik-Historie/Aggregation über mehrere Replays hinweg
- Keine Retention-Policy für Snapshot-Index bei sehr langen Timelines

### Nächster Schritt
Cycle 021: Delta-basiertes Merge-Event-Modell skizzieren und Kostenvergleich materialisiert vs delta vorbereiten.

