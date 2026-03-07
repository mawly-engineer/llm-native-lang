version: 1
document: EXAMPLE_APP_FLOW
purpose: Deterministic end-to-end source -> runtime patch -> replay artifact example.

example:
  entrypoint: python3 -m runtime.example_app_flow
  default_programs:
    - "let x = 1 in x"
    - "let x = 2 in x"
    - "let y = 7 in y"

flow:
  - parse_and_eval_source
  - build_program_run_patch
  - apply_patch_to_program_graph
  - emit_ui_patch_artifact
  - replay_ui_timeline_with_metrics
  - replay_same_programs_on_fresh_runtime
  - compare_ops_and_metrics_for_determinism

artifact_contract:
  required_top_level_fields:
    - programs
    - runs
    - replay
    - determinism_proof
  replay_required_fields:
    - head
    - snapshot_head
    - ops
    - metrics
  determinism_proof_required_fields:
    - ops_equal
    - events_replayed_equal
    - events_total_equal

success_criteria:
  - determinism_proof.ops_equal == true
  - determinism_proof.events_replayed_equal == true
  - determinism_proof.events_total_equal == true
