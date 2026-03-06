# LANGUAGE_BACKLOG.md

## Buckets

### CORE (Language-Core)
- LNG-CORE-01: Freeze minimal grammar (expr, let, if, fn, call)
- LNG-CORE-02: AST schema + invariants
- LNG-CORE-03: Type/check contracts for core nodes

### RUNTIME (Interpreter)
- LNG-RT-01: Deterministic evaluator for core AST
- LNG-RT-02: Environment/scope model with lexical bindings
- LNG-RT-03: Structured runtime errors (code/message/location)

### VALIDATION (Toolchain)
- LNG-VAL-01: Golden program suite (happy path)
- LNG-VAL-02: Golden error suite (type/runtime/parse)
- LNG-VAL-03: Property/fuzz checks for parser/eval invariants

### INTEGRATION
- LNG-INT-01: Bridge interpreter execution to runtime patch flow
- LNG-INT-02: UI/Timeline hooks for language-run artifacts
- LNG-INT-03: End-to-end deterministic replay tests

## Working Rules
- Prefer 1 backlog item per run.
- Mark items in run output: `backlog_item_id` + progress status.
- If blocked, record `BLOCKED` with concrete dependency.
