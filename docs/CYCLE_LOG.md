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
