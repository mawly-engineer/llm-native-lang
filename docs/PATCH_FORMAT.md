# KAIRO Patch Format v0.1

Alle Änderungen laufen über `PatchEnvelope`.

```json
{
  "patch_id": "p-20260306-0001",
  "base_revision": "r-41",
  "target": "program_graph",
  "ops": [
    {"op":"add_node","path":"/modules/-","value":{"id":"workflow.auto","type":"WorkflowEngine"}},
    {"op":"add_edge","path":"/edges/-","value":{"from":"workflow.auto","to":"ui.shared","contract":"ActionModel"}}
  ],
  "policy_context": {"actor":"llm","scope":"shared"},
  "signature": "optional"
}
```

## Op-Typen
- `add_node`
- `remove_node`
- `replace_node`
- `add_edge`
- `remove_edge`
- `set_attr`
- `ui_patch` (UI-Baum)
- `state_patch` (State-Delta)

## Invarianten
- Kein Node ohne Typ
- Keine dangling edges
- Policy-Check vor Commit
- Patch muss gegen `base_revision` validieren

## Merge-Strategie
- Default: 3-way merge auf Revisionsgraph
- Konfliktarten: structural / semantic / policy
- Konflikte erzeugen `merge_proposal` statt blindem Commit
