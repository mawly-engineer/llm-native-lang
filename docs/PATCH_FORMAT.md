version: 1
document: PATCH_FORMAT
purpose: Canonical patch envelope and operation contract.

patch_envelope:
  required_fields:
    - target
    - base_revision
    - ops
  allowed_target_values:
    - program

operations:
  add_node:
    required_fields: [node]
  add_edge:
    required_fields: [edge]
  replace_node:
    required_fields: [node]
  remove_node:
    required_fields: [id]
  remove_edge:
    required_fields: [from, to, contract]
  set_attr:
    required_fields: [node_id, key, value]
  ui_patch:
    required_fields: [ops]

invariants:
  - ops_must_be_non_empty
  - references_must_resolve_or_be_created_within_same_patch
  - apply_is_atomic_all_or_nothing
