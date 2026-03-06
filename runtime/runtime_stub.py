"""KAIRO Runtime Stub v0.2
Minimales Skelett für graphbasierte Ausführung + Patch-Verarbeitung
mit einfachen Typ-/Constraint-Checks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class Revision:
    id: str
    parent: str | None
    graph: Dict[str, Any]


@dataclass
class RuntimeState:
    revisions: Dict[str, Revision] = field(default_factory=dict)
    head: str | None = None


class PatchError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class KairoRuntime:
    def __init__(self) -> None:
        self.state = RuntimeState()
        base_graph = {"modules": [], "edges": []}
        base = Revision(id="r-0", parent=None, graph=base_graph)
        self.state.revisions[base.id] = base
        self.state.head = base.id

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
        existing_nodes: Set[str] = {
            n.get("id") for n in current.graph.get("modules", []) if isinstance(n, dict)
        }
        pending_add_nodes: Set[str] = set()

        for idx, op in enumerate(ops):
            if not isinstance(op, dict):
                raise PatchError("E_OP_TYPE", f"op[{idx}] must be an object")
            kind = op.get("op")
            value = op.get("value")

            if kind == "add_node":
                self._validate_node_shape(value)
                node_id = value["id"]
                if node_id in existing_nodes or node_id in pending_add_nodes:
                    raise PatchError("E_NODE_DUPLICATE", f"duplicate node id: {node_id}")
                pending_add_nodes.add(node_id)

            elif kind == "add_edge":
                self._validate_edge_shape(value)
                source = value["from"]
                target = value["to"]
                known_nodes = existing_nodes | pending_add_nodes
                if source not in known_nodes or target not in known_nodes:
                    raise PatchError(
                        "E_EDGE_DANGLING",
                        f"edge references unknown node(s): from={source}, to={target}",
                    )
            else:
                raise PatchError("E_OP_UNSUPPORTED", f"unsupported op in stub: {kind}")

    def apply_patch(self, patch: Dict[str, Any]) -> str:
        self.validate_patch(patch)
        current = self.state.revisions[self.state.head]  # type: ignore[index]
        new_graph = {
            "modules": list(current.graph.get("modules", [])),
            "edges": list(current.graph.get("edges", [])),
        }

        for op in patch["ops"]:
            kind = op.get("op")
            value = op.get("value")
            if kind == "add_node":
                new_graph["modules"].append(value)
            elif kind == "add_edge":
                new_graph["edges"].append(value)

        new_id = f"r-{len(self.state.revisions)}"
        rev = Revision(id=new_id, parent=self.state.head, graph=new_graph)
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
