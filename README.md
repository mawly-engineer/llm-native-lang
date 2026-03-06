# LLM-Native Language (working title: KAIRO)

Ziel: Eine maschinenoptimierte, LLM-native Programmiersprache mit graphbasierter Architektur, Live-UI, semantischem Datensystem und patch-basierter Evolution.

## Kernprinzipien
- Machine-first Syntax (nicht human-first)
- Program = gerichteter Modulgraph
- Alle Änderungen via strukturierte Patches
- UI als Shared Interaction Space (User + LLM)
- Laufzeit mit inkrementellen UI-Updates (kein Full Reload)
- Native multimodale Dateiverarbeitung
- Policy-first Ausführung in Sandbox

## Verzeichnis
- `docs/SPEC.md` — Sprachspezifikation (v0.1)
- `docs/RUNTIME.md` — Runtime-Architektur (v0.1)
- `docs/PATCH_FORMAT.md` — Patch-Format + Semantik
- `docs/CYCLE_LOG.md` — Iterationshistorie
- `docs/NEXT_STEPS.md` — konkrete nächste Zyklen
- `runtime/runtime_stub.py` — Runtime-Skelett

## Entwicklungsmodus
- Iterativer 15-Minuten-Zyklus
- Pro Zyklus: mindestens eine Architektur-/Runtime-/Syntax-Verbesserung
- Lücken dokumentieren, dann gezielt schließen
