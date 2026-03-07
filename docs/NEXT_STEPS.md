version: 1
document: NEXT_STEPS
purpose: Ordered executable queue for upcoming coordinator cycles.

queue:
  - step_id: STEP-036
    backlog_reference: LNG-VAL-01
    owner_focus: validation
    goal: Add explicit profile-delta assertions for events_total.
    status: done

  - step_id: STEP-037
    backlog_reference: LNG-RT-02
    owner_focus: interpreter-runtime
    goal: Expand lexical scope model and deterministic tests.
    status: done

  - step_id: STEP-038
    backlog_reference: LNG-INT-03
    owner_focus: integration
    goal: Add full end-to-end deterministic replay checks.
    status: done

  - step_id: STEP-039
    backlog_reference: LNG-CORE-04
    owner_focus: language-core
    goal: Add deterministic AST source-span metadata for core nodes with contract tests.
    status: done

  - step_id: STEP-040
    backlog_reference: LNG-CORE-05
    owner_focus: language-core
    goal: Add unary negation grammar and AST contract coverage with deterministic precedence behavior.
    status: done

  - step_id: STEP-041
    backlog_reference: LNG-CORE-06
    owner_focus: language-core
    goal: Add additive/multiplicative binary grammar and deterministic precedence AST contract coverage.
    status: done

  - step_id: STEP-042
    backlog_reference: LNG-CORE-07
    owner_focus: language-core
    goal: Add equality/comparison grammar tiers and deterministic precedence AST contract coverage.
    status: done

  - step_id: STEP-043
    backlog_reference: LNG-CORE-08
    owner_focus: language-core
    goal: Add logical and/or grammar tiers with deterministic short-circuit AST contract coverage.
    status: done

  - step_id: STEP-044
    backlog_reference: LNG-CORE-09
    owner_focus: language-core
    goal: Update SPEC language_minimal_grammar nonterminals/productions so precedence tiers match implemented grammar contracts and tests.
    status: done
