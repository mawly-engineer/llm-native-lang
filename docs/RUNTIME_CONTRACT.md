# KAIRO Runtime Contract v0.1 (Draft)

## Ziel
Zentraler Vertrag für Runtime-Fehlercodes und Query-Semantik.

## Fehlercodes

### Patch/Envelope
- `E_PATCH_TYPE` – Patch ist kein Objekt
- `E_PATCH_REQUIRED` – Pflichtfeld fehlt
- `E_PATCH_ID` – `patch_id` ungültig
- `E_BASE_REV` – `base_revision` ungültig
- `E_TARGET` – `target` ungültig
- `E_BASE_MISMATCH` – Patch basiert nicht auf aktuellem Head
- `E_TARGET_UNSUPPORTED` – nicht unterstütztes Target
- `E_OPS_EMPTY` – keine Ops vorhanden

### Ops / Struktur
- `E_OP_TYPE` – Op ist kein Objekt
- `E_OP_UNSUPPORTED` – Op-Typ nicht unterstützt
- `E_TYPE_NODE` – Node-Value nicht Objekt
- `E_NODE_ID` – Node `id` ungültig
- `E_NODE_TYPE` – Node `type` ungültig
- `E_NODE_DUPLICATE` – Node-ID kollidiert
- `E_NODE_NOT_FOUND` – referenzierte Node existiert nicht
- `E_NODE_IN_USE` – Node hat noch abhängige Edges
- `E_TYPE_EDGE` – Edge-Value nicht Objekt
- `E_EDGE_FROM` – Edge `from` ungültig
- `E_EDGE_TO` – Edge `to` ungültig
- `E_EDGE_CONTRACT` – Edge `contract` ungültig
- `E_EDGE_DANGLING` – Edge verweist auf unbekannte Node
- `E_EDGE_DUPLICATE` – identische Edge bereits vorhanden
- `E_EDGE_NOT_FOUND` – zu entfernende Edge existiert nicht

### Attribute
- `E_ATTR_SHAPE` – `set_attr` hat ungültiges Value-Objekt
- `E_ATTR_NODE` – `set_attr.node_id` ungültig
- `E_ATTR_KEY` – `set_attr.key` ungültig
- `E_ATTR_VALUE` – `set_attr.value` fehlt
- `E_ATTR_RESERVED` – Versuch, reservierte Felder (`id`, `type`) zu überschreiben
- `E_ATTR_CONTAINER` – bestehendes `attrs` Feld ist kein Objekt

### Query
- `E_QUERY_SELECTOR` – Selector ungültig oder Query-Argumente falsch
- `E_QUERY_KEY` – Query-Filter-/Sortierfeld ist für Collection nicht erlaubt
- `E_QUERY_GRAPH` – `modules`/`edges` im Graph haben ungültigen Typ
- `E_QUERY_SORT` – Sortierparameter (`sort_by`, `descending`) ungültig
- `E_QUERY_LIMIT` – `limit` ist kein Integer >= 0

### UI Diff Normalisierung
- `E_UI_OPS_TYPE` – UI-Op-Liste ist kein Array
- `E_UI_OP_SHAPE` – einzelner UI-Op ist kein Objekt
- `E_UI_OP_KIND` – UI-Op-Typ nicht unterstützt
- `E_UI_OP_PATH` – `path` fehlt oder ist leer
- `E_UI_OP_KEY` – `set_prop.key` fehlt oder ist leer

### UI Timeline / Replay
- `E_UI_BASE_MISMATCH` – UI-Patch basiert nicht auf aktuellem UI-Head
- `E_UI_REVISION` – referenzierte UI-Revision unbekannt oder Timeline inkonsistent

## Query-Semantik (v0.1)

### Signatur
- `query(selector, sort_by=None, descending=False, limit=None)`
- `query(graph, selector, sort_by=None, descending=False, limit=None)`

Wenn `graph` fehlt, wird die aktuelle Head-Revision verwendet.

### Ausführung
1. Collection + optionalen Filter aus Selector parsen
2. Elemente der Collection laden (`modules` oder `edges`)
3. Optional filtern (`=`, `!=`, `^=`, `*=`)
4. Optional sortieren über `sort_by`
5. Optional begrenzen über `limit`

### Sortierung
- Aufsteigend per Default (`descending=False`)
- Deterministisch über Python `sorted(...)`
- Vergleich erfolgt als String-Repräsentation
- Fehlende Werte werden als leerer String behandelt
- Für Module sind auch Attributpfade erlaubt: `sort_by="attr.<key>"`

### Limit
- `None` = unbegrenzt
- `0` = leeres Ergebnis
- `n > 0` = erste `n` Elemente nach Filter + Sort
