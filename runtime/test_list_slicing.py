"""Tests for list slicing operator [start:end:step]."""

import pytest
from runtime.ast_contract import AST_SCHEMA, validate_ast
from runtime.interpreter_runtime import eval_expr, EvalError


def make_slice_node(target_items, start=None, end=None, step=None):
    """Helper to create a slice AST node."""
    node = {
        "kind": "slice",
        "span": {"start": 0, "end": 10},
        "target": {"kind": "list", "span": {"start": 0, "end": 10}, "items": target_items},
        "start": start,
        "end": end,
        "step": step,
    }
    return node


def make_number(value):
    return {"kind": "number", "span": {"start": 0, "end": 1}, "value": value}


class TestSliceSchema:
    """Test that slice node conforms to AST schema."""

    def test_slice_in_schema(self):
        assert "slice" in AST_SCHEMA["nodes"]
        node_def = AST_SCHEMA["nodes"]["slice"]
        assert "target" in node_def["fields"]
        assert "start" in node_def["fields"]
        assert "end" in node_def["fields"]
        assert "step" in node_def["fields"]

    def test_slice_validation_basic(self):
        """Slice node validates with all fields present."""
        node = make_slice_node(
            target_items=[make_number(1), make_number(2), make_number(3)],
            start=make_number(0),
            end=make_number(2),
            step=make_number(1),
        )
        validate_ast(node)  # Should not raise

    def test_slice_validation_null_fields(self):
        """Slice node accepts null for optional bounds."""
        node = make_slice_node(
            target_items=[make_number(1), make_number(2)],
            start=None,
            end=None,
            step=None,
        )
        validate_ast(node)  # Should not raise


class TestSliceRuntime:
    """Test slice evaluation semantics."""

    def test_slice_basic_positive_indices(self):
        """Basic slice [1:3] returns elements at index 1 and 2."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 10},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 20},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 30},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 40},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
            "step": None,
        }
        result = eval_expr(node)
        assert result == [20, 30]

    def test_slice_negative_start(self):
        """Slice [-2:] returns last 2 elements."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 4},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": -2},
            "end": None,
            "step": None,
        }
        result = eval_expr(node)
        assert result == [3, 4]

    def test_slice_negative_end(self):
        """Slice [:-1] returns all except last element."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                ],
            },
            "start": None,
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": -1},
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2]

    def test_slice_with_step(self):
        """Slice [::2] returns every second element."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 4},
                ],
            },
            "start": None,
            "end": None,
            "step": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
        }
        result = eval_expr(node)
        assert result == [0, 2, 4]

    def test_slice_negative_step(self):
        """Slice [::-1] reverses the list."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                ],
            },
            "start": None,
            "end": None,
            "step": {"kind": "number", "span": {"start": 0, "end": 1}, "value": -1},
        }
        result = eval_expr(node)
        assert result == [3, 2, 1]

    def test_slice_empty_result(self):
        """Slice [2:2] returns empty list."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
            "step": None,
        }
        result = eval_expr(node)
        assert result == []

    def test_slice_out_of_bounds_clamped(self):
        """Slice bounds are clamped to list size."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 100},
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2]

    def test_slice_zero_step_error(self):
        """Slice with step=0 raises error."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                ],
            },
            "start": None,
            "end": None,
            "step": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(node)
        assert "step" in str(exc_info.value).lower() or "zero" in str(exc_info.value).lower()

    def test_slice_non_list_target_error(self):
        """Slice on non-list raises type error."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 42},
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
            "step": None,
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(node)
        assert "list" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()

    def test_slice_non_int_bounds_error(self):
        """Slice with non-int bounds raises type error."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                ],
            },
            "start": {"kind": "string", "span": {"start": 0, "end": 1}, "value": "hello"},
            "end": None,
            "step": None,
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(node)
        assert "int" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()


class TestSliceEdgeCases:
    """Edge cases for slice operator."""

    def test_slice_full_copy(self):
        """Slice [:] returns a copy of the list."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                ],
            },
            "start": None,
            "end": None,
            "step": None,
        }
        result = eval_expr(node)
        assert result == [1, 2]

    def test_slice_negative_indices_both(self):
        """Slice [-3:-1] works correctly."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 4},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": -3},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": -1},
            "step": None,
        }
        result = eval_expr(node)
        assert result == [2, 3]

    def test_slice_start_greater_than_end(self):
        """Slice [3:1] returns empty list with positive step."""
        node = {
            "kind": "slice",
            "span": {"start": 0, "end": 10},
            "target": {
                "kind": "list",
                "span": {"start": 0, "end": 10},
                "items": [
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 0},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 2},
                    {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
                ],
            },
            "start": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 3},
            "end": {"kind": "number", "span": {"start": 0, "end": 1}, "value": 1},
            "step": None,
        }
        result = eval_expr(node)
        assert result == []
