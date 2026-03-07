version: 2
document: SUPERVISOR_PROFILES
purpose: Define three supervisor roles for staged backlog growth and quality control across multiple cycles.

profiles:
  - profile_id: SUP-CREATOR-01
    name: Backlog Creator Supervisor
    mission: Create one new high-value, testable task when expansion is needed.
    responsibilities:
      - detect gaps from SPEC, RUNTIME, RUNTIME_CONTRACT, recent CYCLE_LOG
      - propose exactly one new backlog item with deterministic scope
      - provide acceptance criteria and suggested focused tests
      - create matching NEXT_STEPS entry
    output_contract:
      required_fields:
        - created_backlog_item_id
        - bucket
        - title
        - priority
        - rationale
        - acceptance_criteria
        - suggested_tests
        - created_next_step_id
    constraints:
      - no vague tasks
      - no multi-epic scope
      - no more than one item per cycle
      - must be implementation-ready

  - profile_id: SUP-VALIDATOR-01
    name: Task Validator Supervisor
    mission: Validate new task quality before execution.
    responsibilities:
      - verify task is deterministic, specific, and test-backed
      - verify acceptance criteria are objectively checkable
      - verify priority and bucket fit current routing signal
      - approve or request revision
    output_contract:
      required_fields:
        - validation_status
        - validation_score
        - passed_checks
        - failed_checks
        - required_fixes
      validation_status_enum:
        - approved
        - needs_revision
        - rejected
    validation_checks:
      - deterministic_scope
      - single_cycle_feasibility
      - testability
      - contract_alignment
      - correct_bucket_and_priority

  - profile_id: SUP-REVISOR-01
    name: Task Revisor Supervisor
    mission: Apply validator-required fixes to the drafted task without changing intent.
    responsibilities:
      - modify drafted backlog item and next_step according to required_fixes
      - preserve deterministic scope and single-cycle feasibility
      - emit revision summary for validator re-check
    output_contract:
      required_fields:
        - revised_backlog_item_id
        - revised_next_step_id
        - applied_fixes
        - unresolved_fixes

workflow:
  mode: staged_multi_cycle
  required_order:
    - create
    - validate
    - revise_if_needed
    - validate_after_revise
    - execute
  execution_rule:
    - exactly one stage per cycle for the same pending item
  retry_rule:
    - if any stage fails or errors, repeat the same stage in the next cycle until success
    - if validator rejects, loop revise -> validate until approved
