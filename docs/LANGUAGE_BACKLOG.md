version: 1
document: LANGUAGE_BACKLOG
purpose: Canonical machine-readable backlog for coordinator-driven execution.

selection_policy:
  per_cycle_execution_limit: 1
  default_pick_order:
    - highest_priority
    - open_status
    - deterministic_id_order

allowed_status_values:
  - open
  - in_progress
  - blocked
  - done

buckets:
  language-core:
    description: Core syntax/AST/type contracts.
    items:
      - id: LNG-CORE-01
        title: Freeze minimal grammar (expr, let, if, fn, call)
        priority: P1
        status: done
      - id: LNG-CORE-02
        title: AST schema and invariants
        priority: P1
        status: done
      - id: LNG-CORE-03
        title: Type/check contracts for core nodes
        priority: P1
        status: done

  interpreter-runtime:
    description: Deterministic interpreter/runtime behavior.
    items:
      - id: LNG-RT-01
        title: Deterministic evaluator for core AST
        priority: P0
        status: done
      - id: LNG-RT-02
        title: Environment/scope model with lexical bindings
        priority: P1
        status: open
      - id: LNG-RT-03
        title: Structured runtime errors (code/message/location)
        priority: P1
        status: open

  validation:
    description: Tests, contracts, and property checks.
    items:
      - id: LNG-VAL-01
        title: Golden program suite
        priority: P1
        status: open
      - id: LNG-VAL-02
        title: Golden error suite
        priority: P1
        status: open
      - id: LNG-VAL-03
        title: Property/fuzz checks for parser/eval invariants
        priority: P2
        status: open

  integration:
    description: End-to-end runtime integration and replay checks.
    items:
      - id: LNG-INT-01
        title: Bridge interpreter execution to runtime patch flow
        priority: P1
        status: open
      - id: LNG-INT-02
        title: UI/timeline hooks for language-run artifacts
        priority: P1
        status: open
      - id: LNG-INT-03
        title: End-to-end deterministic replay tests
        priority: P1
        status: open
