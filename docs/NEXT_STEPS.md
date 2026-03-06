# Next Steps

## Cycle 006
- UI Diff Protocol (deterministische Reihenfolge, conflict-safe)
- Event-Sourcing Modell für State + UI Timeline
- Rollback-Strategie mit Testfällen validieren

## Cycle 007
- Query DSL um Operatoren erweitern (`!=`, Prefix/Contains)
- Query-Operatoren mit Unit-Tests absichern
- Type-System-Doku auf neuen Query-Stand bringen

## Cycle 008
- Fehlercodes in eigenes Runtime-Contract-Dokument extrahieren ✅
- Sortierungs-/Limit-Semantik für Query API definieren ✅
- UI Diff Protocol (deterministische Reihenfolge, conflict-safe) vorbereiten

## Cycle 009
- UI Diff Protocol v0.1 als separates Dokument konkretisieren ✅
- Deterministische Op-Reihenfolge + Konfliktregeln definieren ✅
- Erste Golden-Tests für Diff-Reihenfolge im Runtime-Stub skizzieren ✅

## Cycle 010
- Parent/Child-Konflikte im UI Diff behandeln (`/a` vs `/a/b`) ✅
- Event-Sourcing-Skizze (append-only UI Timeline) dokumentieren ✅
- Rollback-Replay-Testfälle im Runtime-Stub vorbereiten ✅

## Cycle 011
- UI Timeline als append-only Runtime-API implementieren ✅
- Replay über frei wählbaren UI-Head ermöglichen ✅
- Rollback-Verhalten mit Tests absichern ✅

## Cycle 012
- `ui_patch` als reguläre Patch-Op in `apply_patch` integrieren
- Program-Revision und UI-Revision transaktional koppeln
- Fehler-/Rollback-Semantik für gemischte Graph+UI-Patches definieren
