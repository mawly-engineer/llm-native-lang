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

## Patch-Validation Fehlercodes (Runtime Stub)

- `E_PATCH_TYPE` – Patch ist kein Objekt
- `E_PATCH_REQUIRED` – Pflichtfeld fehlt
- `E_PATCH_ID` – `patch_id` ungültig
- `E_BASE_REV` – `base_revision` ungültig
- `E_TARGET` – `target` ungültig
- `E_BASE_MISMATCH` – Patch basiert nicht auf aktuellem Head
- `E_TARGET_UNSUPPORTED` – nicht unterstütztes Target
- `E_OPS_EMPTY` – keine Ops vorhanden
- `E_OP_TYPE` – Op ist kein Objekt
- `E_OP_UNSUPPORTED` – Op-Typ nicht unterstützt
- `E_TYPE_NODE` – Node-Value nicht Objekt
- `E_NODE_ID` – Node `id` ungültig
- `E_NODE_TYPE` – Node `type` ungültig
- `E_NODE_DUPLICATE` – Node-ID kollidiert
- `E_TYPE_EDGE` – Edge-Value nicht Objekt
- `E_EDGE_FROM` – Edge `from` ungültig
- `E_EDGE_TO` – Edge `to` ungültig
- `E_EDGE_CONTRACT` – Edge `contract` ungültig
- `E_EDGE_DANGLING` – Edge verweist auf unbekannte Node
- `E_EDGE_DUPLICATE` – identische Edge bereits vorhanden
- `E_EDGE_NOT_FOUND` – zu entfernende Edge existiert nicht
- `E_NODE_NOT_FOUND` – referenzierte Node existiert nicht
- `E_NODE_IN_USE` – Node hat noch abhängige Edges
- `E_ATTR_SHAPE` – `set_attr` hat ungültiges Value-Objekt
- `E_ATTR_NODE` – `set_attr.node_id` ungültig
- `E_ATTR_KEY` – `set_attr.key` ungültig
- `E_ATTR_VALUE` – `set_attr.value` fehlt
- `E_ATTR_RESERVED` – Versuch, reservierte Felder (`id`, `type`) zu überschreiben
- `E_ATTR_CONTAINER` – bestehendes `attrs` Feld ist kein Objekt
- `E_QUERY_SELECTOR` – Query-Selector ist leer oder syntaktisch ungültig
- `E_QUERY_KEY` – Query-Filterfeld ist für Collection nicht erlaubt
- `E_QUERY_GRAPH` – `modules`/`edges` im Graph haben ungültigen Typ

## Scope v0.1
- Nur `program_graph`
- Unterstützte Ops: `add_node`, `replace_node`, `remove_node`, `add_edge`, `remove_edge`, `set_attr`
- Read-only Query DSL: `modules`/`edges` mit optionalem Equality-Filter auf Kernfeldern
- Ziel: frühe Integritätschecks vor Commit + deterministische Graph-Inspektion

## Nächster Ausbau
- Typ-Registry (bekannte Modulklassen)
- Query-DSL Typableitung
- Policy-abhängige Constraints (scope/actor)
