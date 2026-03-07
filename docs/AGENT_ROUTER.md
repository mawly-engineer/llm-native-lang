version: 2
document: AGENT_ROUTER
purpose: Route the single coordinator to the correct specialist focus each cycle.
updated_at_utc: "2026-03-07T11:41:00Z"

operating_mode:
  scheduler_model: single_coordinator
  coordinator_executes_work_directly: true
  one_backlog_item_per_cycle: true
  dynamic_bucket_selection: true

strategic_targets:
  objective: Raise weakest dimensions first while preserving determinism.
  dimensions:
    language-core:
      score_current: 4
      score_target: 8
    ecosystem:
      score_current: 2
      score_target: 7
    practical-value:
      score_current: 3
      score_target: 7
  priority_rule: Prefer the lowest current score when no blocking reliability signal exists.

active_selection:
  active_primary: ecosystem
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
    reason: "Determinism/runtime correctness is a hard gate."

  - id: route_ecosystem_on_gap
    when:
      signal_ecosystem_gap: true
    select_primary: ecosystem
    reason: "Public usability and project adoption need focused improvement."

  - id: route_practical_value_on_gap
    when:
      signal_practical_value_gap: true
    select_primary: practical-value
    reason: "Hands-on utility and evidence must improve."

  - id: default_route_by_lowest_dimension_score
    when:
      fallback_default: true
    select_primary: lowest_score_dimension
    reason: "By default, advance whichever strategic dimension is currently weakest (ecosystem -> practical-value -> language-core)."

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
