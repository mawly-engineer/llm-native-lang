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
- `E_UI_PATCH_SHAPE` – `ui_patch`-Value oder `ops`-Feld ist ungültig
- `E_UI_BASE_REV` – `ui_patch.base_revision` ist ungültig
- `E_UI_BASE_MISMATCH` – UI-Patch basiert nicht auf aktuellem UI-Head
- `E_UI_REVISION` – referenzierte UI-Revision unbekannt oder Timeline inkonsistent

### UI Merge
- `E_UI_MERGE_POLICY` – nicht unterstützte Merge-Policy angefordert
- `E_UI_MERGE_BASE` – angegebene Base ist kein gemeinsamer Vorfahre beider Branches
- `E_UI_MERGE_CONFLICT` – expliziter Konflikt erkannt (beide Branches ändern denselben Op-Key unterschiedlich)
- `E_UI_MERGE_RESOLUTION` – Resolver-Einträge (`resolutions`/`resolution_notes`) haben ungültiges Format oder ungültige Entscheidung

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

## Gemischte Graph+UI Patches (Cycle 012/013)
- `ui_patch` ist als reguläre Op im Program-Patch erlaubt.
- Der Stub unterstützt mehrere `ui_patch`-Ops pro Patch.
- `ui_patch.value` erwartet:
  - `ops`: non-empty UI-Op-Liste
  - optional `base_revision`: UI-Revision, default = aktueller (simulierter) UI-Head im laufenden Patch
- Mehrere `ui_patch`-Ops werden sequenziell validiert und aufeinander fortgeschrieben.
- Validierung ist transaktional: Jeder Fehler (inkl. UI-Base-Mismatch) verwirft den gesamten Patch.
- Erfolgreiche Program-Revisionen persistieren die resultierende `ui_revision` für deterministisches Replay/Debugging.

## UI Merge-Validierung und Merge-Operation (Cycle 016-018)
- `preview_ui_merge(left_revision, right_revision, base_revision=None, policy="explicit_conflict", resolutions=None, resolution_notes=None)`
  - liefert strukturierte Merge-Information inkl. `conflicts[]`, `applied_resolutions[]` und `merged_ops`
  - `resolutions[]` ist optionales Decision-Log pro Konflikt-Key (`op`, `path`, optional `prop`) mit `decision` in `{accept_left, accept_right}`
  - mutiert keine Timeline
- `validate_ui_merge(...)`
  - nutzt dieselbe Logik, bricht aber bei verbleibenden Konflikten mit `E_UI_MERGE_CONFLICT` ab
  - `PatchError.details` enthält `{ "conflicts": [...] }` für maschinenlesbare Fehleranalyse
- `merge_ui_branches(...)`
  - akzeptiert denselben optionalen Resolver-Input wie `preview_ui_merge(...)`
  - erzeugt eine neue UI-Revision `merged_revision` mit expliziten Branch-Parents:
    - `parent` = linker Branch-Head
    - `secondary_parent` = rechter Branch-Head
  - `resolution_notes` wird im Merge-Event persistiert (Audit-/Decision-Log)
  - setzt `ui_head` auf die neue Merge-Revision
- Ohne `base_revision` wird automatisch der nächste gemeinsame Vorfahre (LCA) im UI-DAG verwendet.
- `base_revision` muss Vorfahre von beiden Branch-Heads sein (`E_UI_MERGE_BASE`) – berücksichtigt `parent` und `secondary_parent`.
- Replay/Snapshot-Auflösung für Merge-Heads erfolgt vorfahrbasiert über den UI-DAG (nicht nur entlang des primären Parents).
- Konfliktregel v0.1 (Policy `explicit_conflict`):
  - Konflikt, wenn beide Branches denselben Op-Key (`op`,`path`,`key`) relativ zur Base unterschiedlich ändern.
  - Kein implizites Last-Writer-Wins über Branches ohne explizite Resolver-Entscheidung.
