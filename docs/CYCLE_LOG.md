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
