version: 1
document: AGENT_ROUTER
purpose: Route the single coordinator to the correct specialist focus each cycle.
updated_at_utc: "2026-03-07T00:15:00Z"

operating_mode:
  scheduler_model: single_coordinator
  coordinator_executes_work_directly: true
  one_backlog_item_per_cycle: true

active_selection:
  active_primary: language-core
  active_secondary: validation

routing_rules_in_priority_order:
  - id: route_integration_on_e2e_red
    when:
      signal_e2e_red: true
    select_primary: integration
    reason: "E2E instability has highest priority."

  - id: route_validation_on_test_failures
    when:
      signal_tests_or_contracts_failing: true
    select_primary: validation
    reason: "Failing assertions/contracts must be stabilized before feature expansion."

  - id: route_runtime_on_runtime_gaps
    when:
      signal_runtime_gap: true
    select_primary: interpreter-runtime
    reason: "Determinism/runtime correctness is currently the main risk area."

  - id: default_route_core
    when:
      fallback_default: true
    select_primary: language-core
    reason: "Advance core language capabilities when no blocking signal exists."

overrides:
  force_agent: null
  hold_agents: []

required_cycle_output_fields:
  - selected_primary
  - selected_secondary
  - executed_backlog_item_id
  - implementation_delta
  - tests
  - changed_files
  - commit
  - blockers
