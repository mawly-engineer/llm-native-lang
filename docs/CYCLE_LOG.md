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
