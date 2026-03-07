version: 1
document: RUNTIME
purpose: Runtime API surface and deterministic behavior guarantees.

runtime_api:
  apply_patch:
    input: [PatchEnvelope]
    output: [revision, ui_revision]

  query:
    input: [selector, sort_by?, descending?, limit?]
    output: [list]

  apply_ui_patch:
    input: [ops, base_revision?]
    output: [ui_revision]

  replay_ui_timeline:
    input: [head?, include_metrics?]
    output: [ops, metrics?]

  create_ui_snapshot:
    input: [head?]
    output: [snapshot_revision]

  preview_ui_merge:
    input: [left_revision, right_revision, base_revision?, policy?, resolutions?]
    output: [merged_ops, conflicts, applied_resolutions]

  merge_ui_branches:
    input: [left_revision, right_revision, base_revision?, mode, resolutions?, resolution_notes?]
    output: [merged_revision, merged_ops, mode, applied_resolutions]

replay_metrics_keys:
  - snapshot_head
  - snapshot_seed_distance
  - events_replayed
  - events_from_snapshot_seed
  - events_total

determinism_guarantees:
  - stable_ui_op_normalization_order
  - deterministic_snapshot_seed_selection
  - order_stability_for_equal_distance_seed_candidates
