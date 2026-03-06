# KAIRO UI Diff Protocol v0.1 (Draft)

## Ziel
Deterministische, konfliktarme Normalisierung von UI-Operationen, bevor sie als `ui_patch` angewendet oder übergeben werden.

## Scope v0.1
Dieser Stand beschreibt nur die Reihenfolge- und Konfliktregeln für einzelne Diff-Listen.
Kein Tree-Merge über mehrere Revisionen, kein Layout-Engine-Verhalten.

## UI-Op-Format
Jede Op ist ein Objekt mit:
- `op`: `remove | replace | move | insert | set_prop`
- `path`: stabiler UI-Knotenpfad (z. B. `/root/header/title`)
- optional `value`
- bei `set_prop` zusätzlich `key` + `value`

## Konfliktregeln
1. **Remove gewinnt auf Pfad + Subtree**
   - Wenn `remove(path)` existiert, werden andere Ops auf diesem Pfad **und allen Kindpfaden** verworfen.
   - Redundante Child-Removes (z. B. `remove(/a/b)` nach `remove(/a)`) werden verworfen.
2. **Last write wins für `set_prop(path,key)`**
   - Bei mehrfachen Writes auf denselben Prop bleibt nur der letzte Wert.
3. **Nicht unterstützte Op-Typen sind Fehler**
   - Runtime muss mit Fehlercode abbrechen.

## Deterministische Reihenfolge
Nach Konfliktreduktion wird stabil sortiert nach:
1. `path` (lexikografisch)
2. Op-Priorität je Pfad:
   - `remove` (0)
   - `replace` (1)
   - `move` (2)
   - `insert` (3)
   - `set_prop` (4)
3. Für `set_prop`: zusätzlich `key` (lexikografisch)

## Warum diese Ordnung?
- reproduzierbare Ergebnisse für Golden-Tests
- geringere Flattereffekte in UI-Streams
- klare, einfache Konfliktauflösung ohne verdeckte Nebenwirkungen

## Testbarkeit
v0.1 erwartet mindestens:
- Golden-Test für gemischte Op-Liste mit identischem Endergebnis nach Normalisierung
- Test für Remove-Übersteuerung auf gleichem Pfad und im Subtree
- Test für Last-Write-Wins bei `set_prop`

## Ausblick v0.2+
- Move-Zyklen und Referenzvalidierung
- Event-Sourcing-Einbindung mit Replay/Rollback
