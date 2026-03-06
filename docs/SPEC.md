# KAIRO Language Spec v0.1

## 1) Programmmodell
Ein Programm ist ein **modularer Wissensgraph**.

```yaml
graph:
  modules:
    - id: data.core
      type: DataSystem
    - id: files.ingest
      type: FileProcessingEngine
    - id: ui.shared
      type: UIEngine
    - id: policy.guard
      type: PolicyEngine
    - id: runtime.core
      type: RuntimeEngine
  edges:
    - from: files.ingest
      to: data.core
      contract: SemanticObject
    - from: data.core
      to: ui.shared
      contract: ViewModel
```

## 2) Primitive Objektklassen
- `Entity`
- `Relationship`
- `Attribute`
- `Embedding`
- `Context`
- `Artifact` (Dateien/Assets)
- `View` (UI-Komponentenbaum)
- `Policy`
- `Workflow`

## 3) Datei-Native Verarbeitung
Jede Datei wird in eine interne Struktur `SemanticObject` überführt:

```json
{
  "artifact_id": "a-123",
  "media_type": "image/png",
  "segments": [
    {"kind":"pixel-region","embedding":"..."},
    {"kind":"caption","text":"..."}
  ],
  "entities": ["invoice","signature"],
  "relations": [{"from":"invoice","to":"signature","type":"contains"}],
  "confidence": 0.91
}
```

## 4) Interaction Space
Drei Sichttypen:
- `user_view`
- `llm_view`
- `shared_view`

Views bestehen aus deklarativen Knoten:
- form
- table
- dashboard
- file_view
- workflow_view
- analysis_panel

## 5) Reaktive Zustände
State ist eventgetrieben:
- `state.<scope>.<key>`
- Ereignisse führen zu Reducer-Updates
- UI wird über Patches inkrementell aktualisiert

## 6) Sicherheitsmodell
Policy Engine erzwingt:
- Zugriffsscoping (read/write/execute)
- Datenraum-Grenzen
- Ressourcenlimits
- Genehmigungs-Policies (z. B. menschliche Freigabe)

## 7) Versionierung
- Jeder Patch erzeugt neue Revision
- Branching: `main`, `exp/*`
- Revisionsgraph statt linearer Historie

## 8) Syntax-Design (Machine-first)
KAIRO nutzt strukturierte Blöcke (JSON/YAML-kompatibel), minimiert Ambiguität, optimiert für deterministische Parsing-Pipelines.
