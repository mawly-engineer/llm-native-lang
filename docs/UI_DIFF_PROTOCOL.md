version: 1
document: UI_DIFF_PROTOCOL
purpose: Deterministic UI diff op schema, conflict rules, and ordering.

allowed_ops:
  - remove
  - replace
  - move
  - insert
  - set_prop

op_schema:
  remove:
    required_fields: [path]
  replace:
    required_fields: [path, value]
  move:
    required_fields: [from, path]
  insert:
    required_fields: [path, value]
  set_prop:
    required_fields: [path, key, value]

conflict_and_order_rules:
  - remove_path_masks_all_descendant_ops
  - repeated_set_prop_same_path_and_key_uses_last_write_wins
  - deterministic_sort_key_is_path_then_op_priority_then_optional_key
