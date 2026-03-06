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


class PatchError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
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

    def replay_ui_timeline(self, head: str | None = None) -> List[Dict[str, Any]]:
        if head is None:
            head = self.ui_head
        if head is not None and head not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {head}")

        ordered_events: List[UITimelineEvent] = []
        cursor = head
        while cursor is not None:
            event = self.ui_timeline.get(cursor)
            if event is None:
                raise PatchError("E_UI_REVISION", f"broken ui timeline at: {cursor}")
            ordered_events.append(event)
            cursor = event.parent

        ops: List[Dict[str, Any]] = []
        for event in reversed(ordered_events):
            ops.extend(deepcopy(event.ops))

        return self.normalize_ui_ops(ops)

    def rollback_ui(self, revision: str | None) -> None:
        if revision is not None and revision not in self.ui_timeline:
            raise PatchError("E_UI_REVISION", f"unknown ui revision: {revision}")
        self.ui_head = revision

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

        ui_patch_seen = False

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
                if ui_patch_seen:
                    raise PatchError("E_UI_PATCH_MULTI", "only one ui_patch op per patch is supported")
                ui_patch_seen = True

                ui_ops, ui_base_revision = self._validate_ui_patch_shape(value)
                resolved_base = self.ui_head if ui_base_revision is None else ui_base_revision
                if resolved_base != self.ui_head:
                    raise PatchError("E_UI_BASE_MISMATCH", "ui base_revision mismatch")
                self.normalize_ui_ops(ui_ops)

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
