"""Tests for object member access operator (.field)."""

import pytest
from runtime.interpreter_runtime import eval_expr, EvalError


class TestMemberAccess:
    """Tests for member_access expression evaluation."""

    def test_basic_member_access(self):
        """Test basic object field access."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 50},
            "name": "person",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 30},
                "entries": [
                    {"key": "name", "value": {"kind": "string", "span": {"start": 11, "end": 17}, "value": "Alice"}},
                    {"key": "age", "value": {"kind": "number", "span": {"start": 24, "end": 26}, "value": 30}},
                ],
            },
            "body": {
                "kind": "member_access",
                "span": {"start": 35, "end": 46},
                "target": {"kind": "ident", "span": {"start": 35, "end": 41}, "name": "person"},
                "member": "name",
            },
        }
        result = eval_expr(ast)
        assert result == "Alice"

    def test_member_access_number_field(self):
        """Test accessing numeric fields."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 50},
            "name": "data",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 30},
                "entries": [
                    {"key": "x", "value": {"kind": "number", "span": {"start": 13, "end": 15}, "value": 42}},
                    {"key": "y", "value": {"kind": "number", "span": {"start": 22, "end": 24}, "value": 100}},
                ],
            },
            "body": {
                "kind": "member_access",
                "span": {"start": 35, "end": 40},
                "target": {"kind": "ident", "span": {"start": 35, "end": 39}, "name": "data"},
                "member": "x",
            },
        }
        result = eval_expr(ast)
        assert result == 42

    def test_member_access_nested(self):
        """Test nested member access (obj.a.b)."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 80},
            "name": "outer",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 50},
                "entries": [
                    {
                        "key": "inner",
                        "value": {
                            "kind": "object",
                            "span": {"start": 20, "end": 45},
                            "entries": [
                                {"key": "value", "value": {"kind": "number", "span": {"start": 30, "end": 32}, "value": 123}},
                            ],
                        },
                    },
                ],
            },
            "body": {
                "kind": "member_access",
                "span": {"start": 55, "end": 70},
                "target": {
                    "kind": "member_access",
                    "span": {"start": 55, "end": 66},
                    "target": {"kind": "ident", "span": {"start": 55, "end": 60}, "name": "outer"},
                    "member": "inner",
                },
                "member": "value",
            },
        }
        result = eval_expr(ast)
        assert result == 123

    def test_member_access_in_expression(self):
        """Test member access within arithmetic expressions."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 60},
            "name": "point",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 35},
                "entries": [
                    {"key": "x", "value": {"kind": "number", "span": {"start": 15, "end": 17}, "value": 10}},
                    {"key": "y", "value": {"kind": "number", "span": {"start": 25, "end": 27}, "value": 20}},
                ],
            },
            "body": {
                "kind": "concat_bin",
                "span": {"start": 40, "end": 55},
                "op": "+",
                "left": {
                    "kind": "member_access",
                    "span": {"start": 40, "end": 46},
                    "target": {"kind": "ident", "span": {"start": 40, "end": 45}, "name": "point"},
                    "member": "x",
                },
                "right": {
                    "kind": "member_access",
                    "span": {"start": 49, "end": 55},
                    "target": {"kind": "ident", "span": {"start": 49, "end": 54}, "name": "point"},
                    "member": "y",
                },
            },
        }
        result = eval_expr(ast)
        assert result == 30

    def test_member_access_missing_field(self):
        """Test error when accessing non-existent field."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 40},
            "name": "obj",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 25},
                "entries": [
                    {"key": "a", "value": {"kind": "number", "span": {"start": 16, "end": 17}, "value": 1}},
                ],
            },
            "body": {
                "kind": "member_access",
                "span": {"start": 30, "end": 38},
                "target": {"kind": "ident", "span": {"start": 30, "end": 33}, "name": "obj"},
                "member": "nonexistent",
            },
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert exc_info.value.code == "E_RT_MISSING_MEMBER"
        assert "nonexistent" in exc_info.value.message

    def test_member_access_non_object(self):
        """Test error when accessing member on non-object."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 30},
            "name": "x",
            "recursive": False,
            "value": {"kind": "number", "span": {"start": 10, "end": 12}, "value": 42},
            "body": {
                "kind": "member_access",
                "span": {"start": 17, "end": 24},
                "target": {"kind": "ident", "span": {"start": 17, "end": 18}, "name": "x"},
                "member": "field",
            },
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert exc_info.value.code == "E_RT_TYPE"
        assert "object" in exc_info.value.message.lower()

    def test_member_access_on_list(self):
        """Test that member access on list raises type error."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 35},
            "name": "lst",
            "recursive": False,
            "value": {
                "kind": "list",
                "span": {"start": 10, "end": 20},
                "items": [
                    {"kind": "number", "span": {"start": 11, "end": 12}, "value": 1},
                    {"kind": "number", "span": {"start": 14, "end": 15}, "value": 2},
                ],
            },
            "body": {
                "kind": "member_access",
                "span": {"start": 25, "end": 33},
                "target": {"kind": "ident", "span": {"start": 25, "end": 28}, "name": "lst"},
                "member": "length",
            },
        }
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert exc_info.value.code == "E_RT_TYPE"

    def test_member_access_string_value(self):
        """Test accessing string field values."""
        ast = {
            "kind": "object",
            "span": {"start": 0, "end": 40},
            "entries": [
                {"key": "greeting", "value": {"kind": "string", "span": {"start": 12, "end": 19}, "value": "hello"}},
                {"key": "target", "value": {"kind": "string", "span": {"start": 30, "end": 36}, "value": "world"}},
            ],
        }
        # Access greeting
        access_ast = {
            "kind": "member_access",
            "span": {"start": 0, "end": 20},
            "target": ast,
            "member": "greeting",
        }
        result = eval_expr(access_ast)
        assert result == "hello"

    def test_member_access_bool_value(self):
        """Test accessing boolean field values."""
        ast = {
            "kind": "object",
            "span": {"start": 0, "end": 35},
            "entries": [
                {"key": "active", "value": {"kind": "bool", "span": {"start": 12, "end": 16}, "value": True}},
                {"key": "verified", "value": {"kind": "bool", "span": {"start": 29, "end": 34}, "value": False}},
            ],
        }
        access_ast = {
            "kind": "member_access",
            "span": {"start": 0, "end": 20},
            "target": ast,
            "member": "active",
        }
        result = eval_expr(access_ast)
        assert result is True

    def test_member_access_null_value(self):
        """Test accessing null field values."""
        ast = {
            "kind": "object",
            "span": {"start": 0, "end": 30},
            "entries": [
                {"key": "empty", "value": {"kind": "null", "span": {"start": 12, "end": 16}, "value": None}},
            ],
        }
        access_ast = {
            "kind": "member_access",
            "span": {"start": 0, "end": 20},
            "target": ast,
            "member": "empty",
        }
        result = eval_expr(access_ast)
        assert result is None

    def test_member_access_list_value(self):
        """Test accessing list field values."""
        ast = {
            "kind": "object",
            "span": {"start": 0, "end": 40},
            "entries": [
                {
                    "key": "items",
                    "value": {
                        "kind": "list",
                        "span": {"start": 12, "end": 25},
                        "items": [
                            {"kind": "number", "span": {"start": 13, "end": 14}, "value": 1},
                            {"kind": "number", "span": {"start": 16, "end": 17}, "value": 2},
                            {"kind": "number", "span": {"start": 19, "end": 20}, "value": 3},
                        ],
                    },
                },
            ],
        }
        access_ast = {
            "kind": "member_access",
            "span": {"start": 0, "end": 20},
            "target": ast,
            "member": "items",
        }
        result = eval_expr(access_ast)
        assert result == [1, 2, 3]

    def test_member_access_object_value(self):
        """Test accessing nested object field values."""
        ast = {
            "kind": "object",
            "span": {"start": 0, "end": 50},
            "entries": [
                {
                    "key": "nested",
                    "value": {
                        "kind": "object",
                        "span": {"start": 15, "end": 35},
                        "entries": [
                            {"key": "deep", "value": {"kind": "number", "span": {"start": 25, "end": 27}, "value": 999}},
                        ],
                    },
                },
            ],
        }
        access_ast = {
            "kind": "member_access",
            "span": {"start": 0, "end": 20},
            "target": ast,
            "member": "nested",
        }
        result = eval_expr(access_ast)
        assert result == {"deep": 999}


class TestMemberAccessWithFunctions:
    """Tests for member access combined with function calls."""

    def test_member_access_then_call(self):
        """Test accessing a function member and calling it."""
        ast = {
            "kind": "let",
            "span": {"start": 0, "end": 100},
            "name": "obj",
            "recursive": False,
            "value": {
                "kind": "object",
                "span": {"start": 10, "end": 60},
                "entries": [
                    {
                        "key": "double",
                        "value": {
                            "kind": "fn",
                            "span": {"start": 25, "end": 55},
                            "params": ["x"],
                            "body": {
                                "kind": "mul_bin",
                                "span": {"start": 45, "end": 52},
                                "left": {"kind": "ident", "span": {"start": 45, "end": 46}, "name": "x"},
                                "right": {"kind": "number", "span": {"start": 49, "end": 50}, "value": 2},
                            },
                        },
                    },
                ],
            },
            "body": {
                "kind": "call",
                "span": {"start": 65, "end": 85},
                "target": {
                    "kind": "member_access",
                    "span": {"start": 65, "end": 79},
                    "target": {"kind": "ident", "span": {"start": 65, "end": 68}, "name": "obj"},
                    "member": "double",
                },
                "args": [
                    {"kind": "number", "span": {"start": 80, "end": 82}, "value": 21},
                ],
            },
        }
        result = eval_expr(ast)
        assert result == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
