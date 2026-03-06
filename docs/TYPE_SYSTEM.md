# KAIRO Type System v0.1 (Draft)

## Ziel
Ein minimales, deterministisches Constraint-System für Runtime-Patch-Validierung.

## Objekt-Schemas

### ModuleNode
```json
{
  "id": "ui.shared",
  "type": "UIEngine"
}
```

Constraints:
- `id`: non-empty string, eindeutig im Graph
- `type`: non-empty string

### ModuleEdge
```json
{
  "from": "files.ingest",
  "to": "data.core",
  "contract": "SemanticObject"
}
```

Constraints:
- `from`, `to`, `contract`: non-empty string
- `from` und `to` müssen auf bekannte Nodes zeigen (bestehend oder innerhalb desselben Patch hinzugefügt)

## Runtime-Fehlercodes

Die vollständige, versionierte Liste liegt jetzt in `docs/RUNTIME_CONTRACT.md`.
Dieses Dokument bleibt auf Typ-/Constraint-Semantik fokussiert.

## Scope v0.1
- Nur `program_graph`
- Unterstützte Ops: `add_node`, `replace_node`, `remove_node`, `add_edge`, `remove_edge`, `set_attr`
- Read-only Query DSL: `modules`/`edges` mit optionalen Operatoren `=`, `!=`, `^=` (Prefix), `*=` (Contains) auf Kernfeldern und `modules[attr.<key>...]`; zusätzlich `sort_by`, `descending`, `limit` als Query-Parameter
- Ziel: frühe Integritätschecks vor Commit + deterministische Graph-Inspektion

## Nächster Ausbau
- Typ-Registry (bekannte Modulklassen)
- Query-DSL Typableitung
- Policy-abhängige Constraints (scope/actor)
