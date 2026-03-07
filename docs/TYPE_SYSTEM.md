version: 1
document: TYPE_SYSTEM
purpose: Structural node/edge constraints and graph invariants.

node_contract:
  required_fields: [id, type]
  attrs_type: object
  attr_key_regex: '^[A-Za-z_][A-Za-z0-9_.-]*$'
  reserved_attr_keys: [id, type]

edge_contract:
  required_fields: [from, to, contract]

graph_invariants:
  - node_id_must_be_unique
  - edge_endpoints_must_resolve
  - node_removal_blocked_if_any_edge_references_node
