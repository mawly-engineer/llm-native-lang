version: 1
document: RUNTIME_CONTRACT
purpose: Error code taxonomy, merge mode semantics, and hard invariants.

error_codes:
  patch:
    - E_PATCH_FORMAT
    - E_PATCH_BASE
    - E_NODE_SCHEMA
    - E_EDGE_SCHEMA
    - E_ATTR_RESERVED

  query:
    - E_QUERY_SELECTOR
    - E_QUERY_KEY
    - E_QUERY_GRAPH
    - E_QUERY_LIMIT

  ui:
    - E_UI_OP
    - E_UI_PATH
    - E_UI_BASE
    - E_UI_REVISION

  merge:
    - E_UI_MERGE_BASE
    - E_UI_MERGE_CONFLICT
    - E_UI_MERGE_POLICY
    - E_UI_MERGE_MODE
    - E_UI_MERGE_RESOLUTION

merge_modes:
  materialized:
    persistence_model: merged_ops
    tradeoff: higher_storage_lower_replay_dependency

  delta:
    persistence_model: delta_ops_plus_delta_base_revision
    tradeoff: lower_storage_higher_replay_dependency

merge_invariants:
  - base_must_be_common_ancestor_of_both_heads
  - unresolved_conflict_must_fail_with_E_UI_MERGE_CONFLICT
  - valid_resolutions_must_produce_deterministic_replay
