version: 1
document: NEXT_STEPS
purpose: Ordered executable queue for upcoming coordinator cycles.

queue:
  - step_id: STEP-036
    backlog_reference: LNG-VAL-01
    owner_focus: validation
    goal: Add explicit profile-delta assertions for events_total.
    status: open

  - step_id: STEP-037
    backlog_reference: LNG-RT-02
    owner_focus: interpreter-runtime
    goal: Expand lexical scope model and deterministic tests.
    status: done

  - step_id: STEP-038
    backlog_reference: LNG-INT-03
    owner_focus: integration
    goal: Add full end-to-end deterministic replay checks.
    status: open
