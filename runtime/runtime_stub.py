"""KAIRO Runtime Stub v0.2
Minimales Skelett für graphbasierte Ausführung + Patch-Verarbeitung
mit einfachen Typ-/Constraint-Checks.
"""

from dataclasses import dataclass, field
from copy import deepcopy
import re
from typing import Any, Dict, List, Set, Tuple


@dataclass
class Revision:
    id: str
    parent: str | None
    graph: Dict[str, Any]
    ui_revision: str | None = None


@dataclass
class RuntimeState:
    revisions: Dict[str, Revision] = field(default_factory=dict)
    head: str | None = None


@dataclass
class UITimelineEvent:
    id: str
    parent: str | None
    ops: List[Dict[str, Any]]
    secondary_parent: str | None = None
    resolution_notes: str | None = None
    merge_mode: str = "materialized"
    delta_base_revision: str | None = None


@dataclass
class UISnapshot:
    id: str
    event_head: str | None
    ops: List[Dict[str, Any]]


class PatchError(Exception):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        self.code = code
        self.details = details
        super().__init__(f"{code}: {message}")


class KairoRuntime:
    ATTR_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
    QUERY_PATTERN = re.compile(
        r"^(modules|edges)(?:\[([a-z_][a-z0-9_.-]*)(=|!=|\^=|\*=)([^\]]+)\])?$"
    )

    def __init__(self) -> None:
        self.state = RuntimeState()
        base_graph = {"modules": [], "edges": []}
        base = Revision(id="r-0", parent=None, graph=base_graph)
        self.state.revisions[base.id] = base
        self.state.head = base.id

        self.ui_timeline: Dict[str, UITimelineEvent] = {}
        self.ui_head: str | None = None
        self.ui_snapshots: Dict[str, UISnapshot] = {}
        self.ui_snapshot_index: Dict[str | None, str] = {}

    def _require_str(self, obj: Dict[str, Any], key: str, code: str) -> str:
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            raise PatchError(code, f"{key} must be a non-empty string")
        return value

    def _validate_node_shape(self, node: Dict[str, Any]) -> None:
        if not isinstance(node, dict):
            raise PatchError("E_TYPE_NODE", "node value must be an object")
        self._require_str(node, "id", "E_NODE_ID")
        self._require_str(node, "type", "E_NODE_TYPE")

    def _validate_edge_shape(self, edge: Dict[str, Any]) -> None:
        if not isinstance(edge, dict):
            raise PatchError("E_TYPE_EDGE", "edge value must be an object")
        self._require_str(edge, "from", "E_EDGE_FROM")
        self._require_str(edge, "to", "E_EDGE_TO")
        self._require_str(edge, "contract", "E_EDGE_CONTRACT")

    def _edge_tuple(self, edge: Dict[str, Any]) -> Tuple[str, str, str]:
        return (edge["from"], edge["to"], edge["contract"])

    def _node_id_from_value(self, value: Any) -> str:
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            return self._require_str(value, "id", "E_NODE_ID")
        raise PatchError("E_NODE_ID", "node reference must be string or object with id")

    def _validate_set_attr_shape(self, value: Any) -> Tuple[str, str, Any]:
        if not isinstance(value, dict):
            raise PatchError("E_ATTR_SHAPE", "set_attr value must be an object")

        node_id = self._require_str(value, "node_id", "E_ATTR_NODE")
        key = self._require_str(value, "key", "E_ATTR_KEY")

        if key in {"id", "type"}:
            raise PatchError("E_ATTR_RESERVED", f"cannot mutate reserved key: {key}")
        if not self.ATTR_KEY_PATTERN.match(key):
            raise PatchError("E_ATTR_KEY", f"invalid attr key: {key}")
        if "value" not in value:
            raise PatchError("E_ATTR_VALUE", "set_attr requires value field")

        return node_id, key, value["value"]

    def _validate_ui_patch_shape(self, value: Any) -> Tuple[List[Dict[str, Any]], str | None]:
        if not isinstance(value, dict):
            raise PatchError("E_UI_PATCH_SHAPE", "ui_patch value must be an object")

        ops = value.get("ops")
        if not isinstance(ops, list) or len(ops) == 0:
            raise PatchError("E_UI_PATCH_SHAPE", "ui_patch.ops must be a non-empty list")

        base_revision = value.get("base_revision")
        if base_revision is not None and (not isinstance(base_revision, str) or not base_revision.strip()):
            raise PatchError("E_UI_BASE_REV", "ui_patch.base_revision must be a non-empty string")

        return ops, base_revision

    def _parse_selector(self, selector: str) -> Tuple[str, str | None, str | None, str | None]:
        if not isinstance(selector, str) or not selector.strip():
            raise PatchError("E_QUERY_SELECTOR", "selector must be a non-empty string")

        match = self.QUERY_PATTERN.match(selector.strip())
        if not match:
            raise PatchError("E_QUERY_SELECTOR", f"invalid selector: {selector}")

        collection, key, operator, value = match.groups()
        return collection, key, operator, value

    def _query_arg_pair(self, *args: Any) -> Tuple[Dict[str, Any], str]:
        if len(args) == 1:
            selector = args[0]
            if self.state.head is None:
                raise PatchError("E_QUERY_GRAPH", "no head revision available")
            graph = self.state.revisions[self.state.head].graph
            return graph, selector

        if len(args) == 2:
            graph, selector = args
            return graph, selector

        raise PatchError("E_QUERY_SELECTOR", "query expects (selector) or (graph, selector)")

    def _validate_query_key(self, collection: str, key: str) -> None:
        allowed_keys = {
            "modules": {"id", "type"},
            "edges": {"from", "to", "contract"},
        }

        if key in allowed_keys[collection]:
            return

        if collection == "modules" and key.startswith("attr.") and len(key) > len("attr."):
            return

        raise PatchError("E_QUERY_KEY", f"selector key '{key}' not allowed for {collection}")

    def _query_obj_matches(
        self,
        collection: str,
        obj: Dict[str, Any],
        key: str,
        operator: str,
        value: str,
    ) -> bool:
        if collection == "modules" and key.startswith("attr."):
            attrs = obj.get("attrs")
            if not isinstance(attrs, dict):
                actual = None
            else:
                attr_key = key[len("attr.") :]
                actual = attrs.get(attr_key)
        else:
            actual = obj.get(key)

        actual_text = "" if actual is None else str(actual)

        if operator == "=":
            return actual_text == value
        if operator == "!=":
            return actual_text != value
        if operator == "^=":
            return actual_text.startswith(value)
        if operator == "*=":
            return value in actual_text

        raise PatchError("E_QUERY_SELECTOR", f"unsupported operator: {operator}")

    def _resolve_sort_value(self, collection: str, obj: Dict[str, Any], sort_key: str) -> str:
        if collection == "modules" and sort_key.startswith("attr."):
            attrs = obj.get("attrs")
            if not isinstance(attrs, dict):
                return ""
            attr_key = sort_key[len("attr.") :]
            value = attrs.get(attr_key)
            return "" if value is None else str(value)

        value = obj.get(sort_key)
        return "" if value is None else str(value)

    def _apply_query_sort(
        self,
        collection: str,
        objects: List[Dict[str, Any]],
        sort_by: str | None,
        descending: bool,
    ) -> List[Dict[str, Any]]:
        if sort_by is None:
            return objects
        if not isinstance(sort_by, str) or not sort_by.strip():
            raise PatchError("E_QUERY_SORT", "sort_by must be a non-empty string")
        if not isinstance(descending, bool):
            raise PatchError("E_QUERY_SORT", "descending must be a boolean")

        self._validate_query_key(collection, sort_by)
        return sorted(
            objects,
            key=lambda obj: self._resolve_sort_value(collection, obj, sort_by),
            reverse=descending,
        )

    def _apply_query_limit(self, objects: List[Dict[str, Any]], limit: int | None) -> List[Dict[str, Any]]:
        if limit is None:
            return objects
        if not isinstance(limit, int) or limit < 0:
            raise PatchError("E_QUERY_LIMIT", "limit must be an integer >= 0")
        return objects[:limit]

    def _is_same_or_descendant_path(self, path: str, anchor: str) -> bool:
        if path == anchor:
            return True
        if anchor == "/":
            return path.startswith("/")
        return path.startswith(anchor + "/")

    def _is_removed_path(self, path: str, removed_paths: Set[str]) -> bool:
        return any(self._is_same_or_descendant_path(path, removed) for removed in removed_paths)

    def normalize_ui_ops(self, ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(ops, list):
            raise PatchError("E_UI_OPS_TYPE", "ui ops must be a list")

        precedence = {
            "remove": 0,
            "replace": 1,
            "move": 2,
            "insert": 3,
            "set_prop": 4,
        }

        reduced: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        removed_paths: Set[str] = set()

        for idx, raw in enumerate(ops):
            if not isinstance(raw, dict):
                raise PatchError("E_UI_OP_SHAPE", f"ui op[{idx}] must be an object")

            kind = raw.get("op")
            path = raw.get("path")
            if kind not in precedence:
                raise PatchError("E_UI_OP_KIND", f"unsupported ui op: {kind}")
            if not isinstance(path, str) or not path.strip():
                raise PatchError("E_UI_OP_PATH", "ui op path must be a non-empty string")

            path = path.strip()
            if kind == "remove":
                if self._is_removed_path(path, removed_paths):
                    continue

                removed_paths.add(path)
                reduced = {
                    k: v
                    for k, v in reduced.items()
                    if not self._is_same_or_descendant_path(k[1], path)
                }
                reduced[(kind, path, "")] = {"op": kind, "path": path}
                continue

            if self._is_removed_path(path, removed_paths):
                continue

            if kind == "set_prop":
                key = raw.get("key")
                if not isinstance(key, str) or not key.strip():
                    raise PatchError("E_UI_OP_KEY", "set_prop requires non-empty key")
                reduced[(kind, path, key)] = {
                    "op": kind,
                    "path": path,
                    "key": key,
                    "value": raw.get("value"),
                }
                continue

            reduced[(kind, path, "")] = {"op": kind, "path": path, "value": raw.get("value")}

        return sorted(
            reduced.values(),
            key=lambda op: (
                op["path"],
                precedence[op["op"]],
                "" if op["op"] != "set_prop" else op["key"],
            ),
        )

    def apply_ui_patch(self, ops: List[Dict[str, Any]], base_revision: str | None = None) -> str:
        if base_revision is None:
            base_revision = self.ui_head
        if base_revision != self.ui_head:
            raise PatchError("E_UI_BASE_MISMATCH", "ui base_revision mismatch")

        normalized = self.normalize_ui_ops(ops)
        new_id = f"u-{len(self.ui_timeline)}"
        self.ui_timeline[new_id] = UITimelineEvent(
            id=new_id,
            parent=self.ui_head,
            ops=deepcopy(normalized),
        )
        self.ui_head = new_id
        return new_id

    def _ui_parent_ids(self, event_id: str | None) -> List[str | None]:
        if event_id is None:
            return []
        event = self.ui_timeline.get(event_id)
        if event is None:
            raise PatchError("E_UI_REVISION", f"broken ui timeline at: {event_id}")

        parents: List[str | None] = []
        if event.parent is not None:
            parents.append(event.parent)
        if event.secondary_parent is not None:
            parents.append(event.secondary_parent)
        return parents

    def _ui_collect_distances(self, head: str | None) -> Dict[str | None, int]:
        distances: Dict[str | None, int] = {}
        if head is None:
            return {None: 0}
        if head not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {head}")

        queue: List[Tuple[str | None, int]] = [(head, 0)]
        while queue:
            node, dist = queue.pop(0)
            if node in distances and dist >= distances[node]:
                continue
            distances[node] = dist
            for parent in self._ui_parent_ids(node):
                queue.append((parent, dist + 1))

        return distances

    def _ui_replay_postorder(self, head: str | None) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()
        visiting: Set[str] = set()

        def visit(node: str | None) -> None:
            if node is None or node in seen:
                return
            if node in visiting:
                raise PatchError("E_UI_REVISION", f"cycle detected in ui timeline at: {node}")

            visiting.add(node)
            for parent in self._ui_parent_ids(node):
                visit(parent)
            visiting.remove(node)
            seen.add(node)
            ordered.append(node)

        visit(head)
        return ordered

    def create_ui_snapshot(self, head: str | None = None) -> str:
        if head is None:
            head = self.ui_head
        if head is not None and head not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {head}")

        ops = self.replay_ui_timeline(head=head)
        snapshot_id = f"s-{len(self.ui_snapshots)}"
        self.ui_snapshots[snapshot_id] = UISnapshot(
            id=snapshot_id,
            event_head=head,
            ops=deepcopy(ops),
        )
        self.ui_snapshot_index[head] = snapshot_id
        return snapshot_id

    def _ui_event_apply_sequence(
        self,
        head: str | None,
        seen: Set[str],
        visiting: Set[str],
        use_snapshot_seed: bool,
    ) -> Tuple[List[Dict[str, Any]], int, str | None, int | None]:
        if head is None:
            return [], 0, None, None
        if head in seen:
            return [], 0, None, None
        if head in visiting:
            raise PatchError("E_UI_REVISION", f"cycle detected in ui timeline at: {head}")
        if head not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {head}")

        visiting.add(head)
        event = self.ui_timeline[head]

        seed_snapshot_head: str | None = None
        seed_snapshot_distance: int | None = None
        seed_ops: List[Dict[str, Any]] = []
        events_replayed = 0

        if event.merge_mode == "delta":
            base_ops, base_count, _snap_head, _snap_distance = self._ui_event_apply_sequence(
                event.delta_base_revision,
                seen,
                visiting,
                use_snapshot_seed,
            )
            ops = base_ops + deepcopy(event.ops)
            events_replayed = base_count + 1
        else:
            if use_snapshot_seed:
                distances = self._ui_collect_distances(head)
                for event_id in distances:
                    snapshot_id = self.ui_snapshot_index.get(event_id)
                    if snapshot_id is None:
                        continue
                    distance = distances[event_id]
                    if seed_snapshot_distance is None or distance < seed_snapshot_distance:
                        seed_snapshot_distance = distance
                        seed_snapshot_head = event_id
                        seed_ops = deepcopy(self.ui_snapshots[snapshot_id].ops)

            parent_ops: List[Dict[str, Any]] = []
            if event.parent is not None:
                left_ops, left_count, _left_snap, _left_dist = self._ui_event_apply_sequence(
                    event.parent,
                    seen,
                    visiting,
                    False,
                )
                parent_ops.extend(left_ops)
                events_replayed += left_count

            if event.secondary_parent is not None:
                right_ops, right_count, _right_snap, _right_dist = self._ui_event_apply_sequence(
                    event.secondary_parent,
                    seen,
                    visiting,
                    False,
                )
                parent_ops.extend(right_ops)
                events_replayed += right_count

            ops = seed_ops + parent_ops + deepcopy(event.ops)
            events_replayed += 1

        visiting.remove(head)
        seen.add(head)

        return ops, events_replayed, seed_snapshot_head, seed_snapshot_distance

    def replay_ui_timeline(
        self,
        head: str | None = None,
        include_metrics: bool = False,
    ) -> List[Dict[str, Any]] | Dict[str, Any]:
        if head is None:
            head = self.ui_head
        if head is not None and head not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {head}")

        ops, events_replayed, snapshot_head, snapshot_distance = self._ui_event_apply_sequence(
            head,
            seen=set(),
            visiting=set(),
            use_snapshot_seed=True,
        )

        postorder = self._ui_replay_postorder(head)
        distances = self._ui_collect_distances(head)
        best_distance: int | None = None
        best_snapshot_head: str | None = None
        for event_id in distances:
            snapshot_id = self.ui_snapshot_index.get(event_id)
            if snapshot_id is None:
                continue
            distance = distances[event_id]
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_snapshot_head = event_id

        replay_ids = postorder
        if best_snapshot_head in distances:
            snapshot_ancestors = self._ui_ancestors(best_snapshot_head)
            replay_ids = [event_id for event_id in postorder if event_id not in snapshot_ancestors]

        normalized_ops = self.normalize_ui_ops(ops)
        replay_count = len(replay_ids) if best_snapshot_head in distances else events_replayed
        metrics = {
            "events_replayed": replay_count,
            "events_from_snapshot_seed": replay_count,
            "events_total": events_replayed,
            "snapshot_seed_distance": best_distance,
        }
        if snapshot_head is None:
            snapshot_head = best_snapshot_head
        if snapshot_distance is None:
            snapshot_distance = best_distance

        if include_metrics:
            return {
                "head": head,
                "snapshot_head": snapshot_head,
                "ops": normalized_ops,
                "metrics": metrics,
            }

        return normalized_ops

    def rollback_ui(self, revision: str | None) -> None:
        if revision is not None and revision not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {revision}")
        self.ui_head = revision

    def _ui_ancestors(self, head: str | None) -> Set[str | None]:
        return set(self._ui_collect_distances(head).keys())

    def _ui_lca(self, left: str | None, right: str | None) -> str | None:
        left_distances = self._ui_collect_distances(left)
        right_distances = self._ui_collect_distances(right)

        common = set(left_distances.keys()) & set(right_distances.keys())
        if not common:
            return None

        ranked = sorted(
            common,
            key=lambda node: (
                left_distances[node] + right_distances[node],
                max(left_distances[node], right_distances[node]),
                "" if node is None else node,
            ),
        )
        return ranked[0]

    def _resolution_key(self, entry: Dict[str, Any]) -> Tuple[str, str, str]:
        if not isinstance(entry, dict):
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolution entry must be an object")

        op = entry.get("op")
        path = entry.get("path")
        prop = entry.get("prop")

        if not isinstance(op, str) or not op.strip():
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolution.op must be a non-empty string")
        if not isinstance(path, str) or not path.strip():
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolution.path must be a non-empty string")
        if prop is not None and not isinstance(prop, str):
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolution.prop must be a string when set")

        return (op, path, "" if prop is None else prop)

    def _resolution_decisions(self, resolutions: List[Dict[str, Any]] | None) -> Dict[Tuple[str, str, str], str]:
        if resolutions is None:
            return {}
        if not isinstance(resolutions, list):
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolutions must be a list")

        decisions: Dict[Tuple[str, str, str], str] = {}
        for entry in resolutions:
            key = self._resolution_key(entry)
            decision = entry.get("decision")
            if decision not in {"accept_left", "accept_right"}:
                raise PatchError(
                    "E_UI_MERGE_RESOLUTION",
                    "resolution.decision must be 'accept_left' or 'accept_right'",
                )
            decisions[key] = decision

        return decisions

    def preview_ui_merge(
        self,
        left_revision: str | None,
        right_revision: str | None,
        base_revision: str | None = None,
        policy: str = "explicit_conflict",
        resolutions: List[Dict[str, Any]] | None = None,
        resolution_notes: str | None = None,
    ) -> Dict[str, Any]:
        if policy != "explicit_conflict":
            raise PatchError("E_UI_MERGE_POLICY", "unsupported ui merge policy")

        for name, revision in (("left", left_revision), ("right", right_revision), ("base", base_revision)):
            if revision is not None and revision not in self.ui_timeline:
                raise PatchError("E_UI_REVISION", f"unknown {name} ui revision: {revision}")

        if resolution_notes is not None and (not isinstance(resolution_notes, str) or not resolution_notes.strip()):
            raise PatchError("E_UI_MERGE_RESOLUTION", "resolution_notes must be a non-empty string")

        resolution_map = self._resolution_decisions(resolutions)
        resolved_base = self._ui_lca(left_revision, right_revision) if base_revision is None else base_revision

        left_ancestors = self._ui_ancestors(left_revision)
        right_ancestors = self._ui_ancestors(right_revision)
        if resolved_base not in left_ancestors or resolved_base not in right_ancestors:
            raise PatchError("E_UI_MERGE_BASE", "base revision must be an ancestor of both branches")

        base_ops = self.replay_ui_timeline(resolved_base)
        left_ops = self.replay_ui_timeline(left_revision)
        right_ops = self.replay_ui_timeline(right_revision)

        def op_key(op: Dict[str, Any]) -> Tuple[str, str, str]:
            return (op.get("op", ""), op.get("path", ""), op.get("key", ""))

        base_map = {op_key(op): op for op in base_ops}
        left_map = {op_key(op): op for op in left_ops}
        right_map = {op_key(op): op for op in right_ops}

        merged_by_key = {op_key(op): deepcopy(op) for op in base_ops}
        merged_by_key.update({op_key(op): deepcopy(op) for op in left_ops})
        merged_by_key.update({op_key(op): deepcopy(op) for op in right_ops})

        conflicts: List[Dict[str, Any]] = []
        applied_resolutions: List[Dict[str, Any]] = []
        all_keys = set(left_map) | set(right_map)
        for key in sorted(all_keys):
            left_op = left_map.get(key)
            right_op = right_map.get(key)
            if left_op is None or right_op is None:
                continue
            if left_op == right_op:
                continue

            base_op = base_map.get(key)
            left_changed = left_op != base_op
            right_changed = right_op != base_op
            if not (left_changed and right_changed):
                continue

            decision = resolution_map.get(key)
            if decision == "accept_left":
                merged_by_key[key] = deepcopy(left_op)
                applied_resolutions.append(
                    {
                        "key": {"op": key[0], "path": key[1], "prop": key[2] or None},
                        "decision": decision,
                    }
                )
                continue
            if decision == "accept_right":
                merged_by_key[key] = deepcopy(right_op)
                applied_resolutions.append(
                    {
                        "key": {"op": key[0], "path": key[1], "prop": key[2] or None},
                        "decision": decision,
                    }
                )
                continue

            conflicts.append(
                {
                    "key": {"op": key[0], "path": key[1], "prop": key[2] or None},
                    "left": deepcopy(left_op),
                    "right": deepcopy(right_op),
                }
            )

        merged_ops = self.normalize_ui_ops(list(merged_by_key.values()))

        return {
            "base_revision": resolved_base,
            "left_revision": left_revision,
            "right_revision": right_revision,
            "policy": policy,
            "conflicts": conflicts,
            "applied_resolutions": applied_resolutions,
            "resolution_notes": resolution_notes,
            "merged_ops": merged_ops,
        }

    def preview_ui_merge_delta(
        self,
        left_revision: str | None,
        right_revision: str | None,
        base_revision: str | None = None,
        policy: str = "explicit_conflict",
        resolutions: List[Dict[str, Any]] | None = None,
        resolution_notes: str | None = None,
    ) -> Dict[str, Any]:
        merge_info = self.preview_ui_merge(
            left_revision=left_revision,
            right_revision=right_revision,
            base_revision=base_revision,
            policy=policy,
            resolutions=resolutions,
            resolution_notes=resolution_notes,
        )

        resolved_base = merge_info["base_revision"]
        base_ops = self.replay_ui_timeline(resolved_base)
        merged_ops = merge_info["merged_ops"]

        def op_key(op: Dict[str, Any]) -> Tuple[str, str, str]:
            return (op.get("op", ""), op.get("path", ""), op.get("key", ""))

        base_map = {op_key(op): op for op in base_ops}
        delta_ops = [op for op in merged_ops if base_map.get(op_key(op)) != op]
        replay_with_delta = self.normalize_ui_ops(base_ops + delta_ops)

        return {
            **merge_info,
            "base_ops": base_ops,
            "delta_ops": delta_ops,
            "delta_metrics": {
                "base_ops": len(base_ops),
                "merged_ops": len(merged_ops),
                "delta_ops": len(delta_ops),
                "reconstructs_merged": replay_with_delta == merged_ops,
            },
        }

    def validate_ui_merge(
        self,
        left_revision: str | None,
        right_revision: str | None,
        base_revision: str | None = None,
        policy: str = "explicit_conflict",
        resolutions: List[Dict[str, Any]] | None = None,
        resolution_notes: str | None = None,
    ) -> Dict[str, Any]:
        merge_info = self.preview_ui_merge(
            left_revision=left_revision,
            right_revision=right_revision,
            base_revision=base_revision,
            policy=policy,
            resolutions=resolutions,
            resolution_notes=resolution_notes,
        )

        conflicts = merge_info["conflicts"]
        if conflicts:
            raise PatchError(
                "E_UI_MERGE_CONFLICT",
                f"ui merge conflict count: {len(conflicts)}",
                details={"conflicts": deepcopy(conflicts)},
            )

        return merge_info

    def merge_ui_branches(
        self,
        left_revision: str | None,
        right_revision: str | None,
        base_revision: str | None = None,
        policy: str = "explicit_conflict",
        resolutions: List[Dict[str, Any]] | None = None,
        resolution_notes: str | None = None,
        mode: str = "materialized",
    ) -> Dict[str, Any]:
        if mode not in {"materialized", "delta"}:
            raise PatchError("E_UI_MERGE_MODE", "merge mode must be 'materialized' or 'delta'")

        if mode == "delta":
            merge_info = self.preview_ui_merge_delta(
                left_revision=left_revision,
                right_revision=right_revision,
                base_revision=base_revision,
                policy=policy,
                resolutions=resolutions,
                resolution_notes=resolution_notes,
            )
            if merge_info["conflicts"]:
                raise PatchError(
                    "E_UI_MERGE_CONFLICT",
                    f"ui merge conflict count: {len(merge_info['conflicts'])}",
                    details={"conflicts": deepcopy(merge_info["conflicts"])} ,
                )
            event_ops = merge_info["delta_ops"]
            delta_base_revision = merge_info["base_revision"]
        else:
            merge_info = self.validate_ui_merge(
                left_revision=left_revision,
                right_revision=right_revision,
                base_revision=base_revision,
                policy=policy,
                resolutions=resolutions,
                resolution_notes=resolution_notes,
            )
            event_ops = merge_info["merged_ops"]
            delta_base_revision = None

        new_id = f"u-{len(self.ui_timeline)}"
        self.ui_timeline[new_id] = UITimelineEvent(
            id=new_id,
            parent=left_revision,
            secondary_parent=right_revision,
            resolution_notes=resolution_notes,
            merge_mode=mode,
            delta_base_revision=delta_base_revision,
            ops=deepcopy(event_ops),
        )
        self.ui_head = new_id

        return {
            **merge_info,
            "merged_revision": new_id,
            "merge_mode": mode,
        }

    def query(
        self,
        *args: Any,
        sort_by: str | None = None,
        descending: bool = False,
        limit: int | None = None,
    ) -> List[Dict[str, Any]]:
        graph, selector = self._query_arg_pair(*args)
        collection, key, operator, value = self._parse_selector(selector)

        if not isinstance(graph, dict):
            raise PatchError("E_QUERY_GRAPH", "graph must be an object")

        items = graph.get(collection)
        if not isinstance(items, list):
            raise PatchError("E_QUERY_GRAPH", f"graph field '{collection}' must be a list")

        objects = [item for item in items if isinstance(item, dict)]
        if key is not None:
            self._validate_query_key(collection, key)
            objects = [
                obj for obj in objects if self._query_obj_matches(collection, obj, key, operator, value)
            ]

        objects = self._apply_query_sort(collection, objects, sort_by, descending)
        return self._apply_query_limit(objects, limit)

    def validate_patch(self, patch: Dict[str, Any]) -> None:
        if not isinstance(patch, dict):
            raise PatchError("E_PATCH_TYPE", "patch must be an object")

        required = ["patch_id", "base_revision", "target", "ops"]
        for key in required:
            if key not in patch:
                raise PatchError("E_PATCH_REQUIRED", f"missing required field: {key}")

        self._require_str(patch, "patch_id", "E_PATCH_ID")
        self._require_str(patch, "base_revision", "E_BASE_REV")
        self._require_str(patch, "target", "E_TARGET")

        if patch["base_revision"] != self.state.head:
            raise PatchError("E_BASE_MISMATCH", "base_revision mismatch")
        if patch["target"] != "program_graph":
            raise PatchError("E_TARGET_UNSUPPORTED", "only target=program_graph is supported in stub")

        ops = patch["ops"]
        if not isinstance(ops, list) or len(ops) == 0:
            raise PatchError("E_OPS_EMPTY", "ops must be a non-empty list")

        current = self.state.revisions[self.state.head]  # type: ignore[index]
        modules = [m for m in current.graph.get("modules", []) if isinstance(m, dict)]
        edges = [e for e in current.graph.get("edges", []) if isinstance(e, dict)]

        known_nodes: Set[str] = {self._require_str(m, "id", "E_NODE_ID") for m in modules}
        known_edges: Set[Tuple[str, str, str]] = set()
        for edge in edges:
            self._validate_edge_shape(edge)
            known_edges.add(self._edge_tuple(edge))

        simulated_ui_head = self.ui_head
        simulated_ui_len = len(self.ui_timeline)

        for idx, op in enumerate(ops):
            if not isinstance(op, dict):
                raise PatchError("E_OP_TYPE", f"op[{idx}] must be an object")
            kind = op.get("op")
            value = op.get("value")

            if kind == "add_node":
                self._validate_node_shape(value)
                node_id = value["id"]
                if node_id in known_nodes:
                    raise PatchError("E_NODE_DUPLICATE", f"duplicate node id: {node_id}")
                known_nodes.add(node_id)

            elif kind == "replace_node":
                self._validate_node_shape(value)
                node_id = value["id"]
                if node_id not in known_nodes:
                    raise PatchError("E_NODE_NOT_FOUND", f"cannot replace unknown node: {node_id}")

            elif kind == "remove_node":
                node_id = self._node_id_from_value(value)
                if node_id not in known_nodes:
                    raise PatchError("E_NODE_NOT_FOUND", f"cannot remove unknown node: {node_id}")

                for source, target, _contract in known_edges:
                    if source == node_id or target == node_id:
                        raise PatchError(
                            "E_NODE_IN_USE",
                            f"cannot remove node with remaining edges: {node_id}",
                        )
                known_nodes.remove(node_id)

            elif kind == "add_edge":
                self._validate_edge_shape(value)
                source, target, contract = self._edge_tuple(value)
                if source not in known_nodes or target not in known_nodes:
                    raise PatchError(
                        "E_EDGE_DANGLING",
                        f"edge references unknown node(s): from={source}, to={target}",
                    )
                edge_key = (source, target, contract)
                if edge_key in known_edges:
                    raise PatchError("E_EDGE_DUPLICATE", f"duplicate edge: {edge_key}")
                known_edges.add(edge_key)

            elif kind == "set_attr":
                node_id, _key, _attr_value = self._validate_set_attr_shape(value)
                if node_id not in known_nodes:
                    raise PatchError("E_NODE_NOT_FOUND", f"cannot set attr on unknown node: {node_id}")

                for mod in modules:
                    if self._require_str(mod, "id", "E_NODE_ID") == node_id:
                        attrs = mod.get("attrs")
                        if attrs is not None and not isinstance(attrs, dict):
                            raise PatchError("E_ATTR_CONTAINER", "node attrs must be an object")
                        break

            elif kind == "remove_edge":
                self._validate_edge_shape(value)
                edge_key = self._edge_tuple(value)
                if edge_key not in known_edges:
                    raise PatchError("E_EDGE_NOT_FOUND", f"cannot remove unknown edge: {edge_key}")
                known_edges.remove(edge_key)

            elif kind == "ui_patch":
                ui_ops, ui_base_revision = self._validate_ui_patch_shape(value)
                resolved_base = simulated_ui_head if ui_base_revision is None else ui_base_revision
                if resolved_base != simulated_ui_head:
                    raise PatchError("E_UI_BASE_MISMATCH", "ui base_revision mismatch")
                self.normalize_ui_ops(ui_ops)
                simulated_ui_head = f"u-{simulated_ui_len}"
                simulated_ui_len += 1

            else:
                raise PatchError("E_OP_UNSUPPORTED", f"unsupported op in stub: {kind}")

    def apply_patch(self, patch: Dict[str, Any]) -> str:
        self.validate_patch(patch)
        current = self.state.revisions[self.state.head]  # type: ignore[index]
        new_graph = {
            "modules": [m.copy() if isinstance(m, dict) else m for m in current.graph.get("modules", [])],
            "edges": [e.copy() if isinstance(e, dict) else e for e in current.graph.get("edges", [])],
        }

        new_ui_revision = self.ui_head

        for op in patch["ops"]:
            kind = op.get("op")
            value = op.get("value")

            if kind == "add_node":
                new_graph["modules"].append(value)

            elif kind == "replace_node":
                node_id = value["id"]
                for i, mod in enumerate(new_graph["modules"]):
                    if isinstance(mod, dict) and mod.get("id") == node_id:
                        new_graph["modules"][i] = value
                        break

            elif kind == "remove_node":
                node_id = self._node_id_from_value(value)
                new_graph["modules"] = [
                    mod
                    for mod in new_graph["modules"]
                    if not (isinstance(mod, dict) and mod.get("id") == node_id)
                ]

            elif kind == "add_edge":
                new_graph["edges"].append(value)

            elif kind == "set_attr":
                node_id, key, attr_value = self._validate_set_attr_shape(value)
                for mod in new_graph["modules"]:
                    if isinstance(mod, dict) and mod.get("id") == node_id:
                        attrs = mod.get("attrs")
                        if attrs is None:
                            attrs = {}
                            mod["attrs"] = attrs
                        elif not isinstance(attrs, dict):
                            raise PatchError("E_ATTR_CONTAINER", "node attrs must be an object")
                        attrs[key] = attr_value
                        break

            elif kind == "remove_edge":
                edge_key = self._edge_tuple(value)
                for i, edge in enumerate(new_graph["edges"]):
                    if isinstance(edge, dict) and self._edge_tuple(edge) == edge_key:
                        del new_graph["edges"][i]
                        break

            elif kind == "ui_patch":
                ui_ops, ui_base_revision = self._validate_ui_patch_shape(value)
                new_ui_revision = self.apply_ui_patch(ui_ops, base_revision=ui_base_revision)

        new_id = f"r-{len(self.state.revisions)}"
        rev = Revision(
            id=new_id,
            parent=self.state.head,
            graph=new_graph,
            ui_revision=new_ui_revision,
        )
        self.state.revisions[new_id] = rev
        self.state.head = new_id
        return new_id


if __name__ == "__main__":
    rt = KairoRuntime()
    patch = {
        "patch_id": "p-1",
        "base_revision": "r-0",
        "target": "program_graph",
        "ops": [
            {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
            {"op": "add_edge", "value": {"from": "ui.shared", "to": "ui.shared", "contract": "self"}},
        ],
    }
    rid = rt.apply_patch(patch)
    print("new revision:", rid)
