"""Tests for optional call operator ?(args) - null-safe function invocation."""

from runtime.interpreter_runtime import eval_expr, EvalError
from runtime.ast_contract import validate_ast


class TestOptionalCall:
    """Test suite for optional call operator ?(args)."""

    def _make_optional_call(self, target_expr, args):
        return {
            "kind": "optional_call",
            "span": {"start": 0, "end": 20},
            "target": target_expr,
            "args": args,
        }

    def _make_ident(self, name):
        return {"kind": "ident", "span": {"start": 0, "end": len(name)}, "name": name}

    def _make_null(self):
        return {"kind": "null", "span": {"start": 0, "end": 4}, "value": None}

    def _make_number(self, value):
        return {"kind": "number", "span": {"start": 0, "end": 10}, "value": value}

    def _make_fn(self, params, body):
        return {"kind": "fn", "span": {"start": 0, "end": 30}, "params": params, "body": body}

    def _make_let(self, name, value, body):
        return {
            "kind": "let",
            "span": {"start": 0, "end": 40},
            "name": name,
            "value": value,
            "body": body,
        }

    def test_null_target_returns_null_without_evaluating_args(self):
        """If target is null, return null without evaluating arguments."""
        # f?(1 + error) should return null without evaluating args
        null_node = self._make_null()
        # This arg would cause error if evaluated
        bad_arg = {
            "kind": "call",
            "span": {"start": 0, "end": 10},
            "target": self._make_ident("undefined_func"),
            "args": [],
        }
        node = self._make_optional_call(null_node, [bad_arg])
        
        validate_ast(node)
        result = eval_expr(node)
        assert result is None

    def test_valid_callable_with_no_args(self):
        """Call a function with no arguments."""
        # fn f() { 42 } f?()
        fn_body = self._make_number(42)
        fn_node = self._make_fn([], fn_body)
        let_node = self._make_let("f", fn_node, self._make_optional_call(self._make_ident("f"), []))
        
        validate_ast(let_node)
        result = eval_expr(let_node)
        assert result == 42

    def test_valid_callable_with_args(self):
        """Call a function with arguments."""
        # fn add(a, b) { a + b } add?(1, 2)
        fn_body = {
            "kind": "concat_bin",
            "span": {"start": 0, "end": 10},
            "op": "+",
            "left": self._make_ident("a"),
            "right": self._make_ident("b"),
        }
        fn_node = self._make_fn(["a", "b"], fn_body)
        let_node = self._make_let(
            "add",
            fn_node,
            self._make_optional_call(
                self._make_ident("add"),
                [self._make_number(1), self._make_number(2)]
            ),
        )
        
        validate_ast(let_node)
        result = eval_expr(let_node)
        assert result == 3

    def test_arity_mismatch_raises_error(self):
        """Wrong number of arguments raises E_RT_ARITY_MISMATCH."""
        # fn f(x) { x } f?(1, 2) should error
        fn_body = self._make_ident("x")
        fn_node = self._make_fn(["x"], fn_body)
        let_node = self._make_let(
            "f",
            fn_node,
            self._make_optional_call(
                self._make_ident("f"),
                [self._make_number(1), self._make_number(2)]
            ),
        )
        
        validate_ast(let_node)
        try:
            eval_expr(let_node)
            assert False, "Expected EvalError"
        except EvalError as e:
            assert e.code == "E_RT_ARITY_MISMATCH"
            assert "optional call arity mismatch" in e.message

    def test_non_callable_non_null_raises_error(self):
        """Non-callable, non-null target raises E_RT_NOT_CALLABLE."""
        # 42?(1) should error
        node = self._make_optional_call(self._make_number(42), [self._make_number(1)])
        
        validate_ast(node)
        try:
            eval_expr(node)
            assert False, "Expected EvalError"
        except EvalError as e:
            assert e.code == "E_RT_NOT_CALLABLE"
            assert "not callable" in e.message

    def test_nested_optional_calls(self):
        """Nested optional calls: fn?(arg1)?(arg2)."""
        # fn outer(x) { fn inner(y) { x + y } } outer?(1)?(2)
        inner_body = {
            "kind": "concat_bin",
            "span": {"start": 0, "end": 10},
            "op": "+",
            "left": self._make_ident("x"),
            "right": self._make_ident("y"),
        }
        inner_fn = self._make_fn(["y"], inner_body)
        outer_body = self._make_let("inner", inner_fn, self._make_ident("inner"))
        outer_fn = self._make_fn(["x"], outer_body)
        
        # outer?(1) returns inner closure, then ?(2) calls it
        first_call = self._make_optional_call(self._make_ident("outer"), [self._make_number(1)])
        nested_call = self._make_optional_call(first_call, [self._make_number(2)])
        let_node = self._make_let("outer", outer_fn, nested_call)
        
        validate_ast(let_node)
        result = eval_expr(let_node)
        assert result == 3

    def test_callable_in_object(self):
        """Call a function value stored in an object."""
        # let obj = { inc: fn(x) { x + 1 } } obj.inc?(5)
        fn_body = {
            "kind": "concat_bin",
            "span": {"start": 0, "end": 10},
            "op": "+",
            "left": self._make_ident("x"),
            "right": self._make_number(1),
        }
        fn_node = self._make_fn(["x"], fn_body)
        obj_node = {
            "kind": "object",
            "span": {"start": 0, "end": 20},
            "entries": [{"key": "inc", "value": fn_node}],
        }
        member_access = {
            "kind": "member_access",
            "span": {"start": 0, "end": 10},
            "target": self._make_ident("obj"),
            "member": "inc",
        }
        call_node = self._make_optional_call(member_access, [self._make_number(5)])
        let_node = self._make_let("obj", obj_node, call_node)
        
        validate_ast(let_node)
        result = eval_expr(let_node)
        assert result == 6

    def test_builtin_callable(self):
        """Call a built-in function (if available in env)."""
        # Built-in functions like is_null should work with ?()
        # This test verifies the runtime handles callable built-ins
        pass  # Built-ins require environment setup, tested in integration

    def test_null_target_no_side_effects(self):
        """Verify null target short-circuits without side effects."""
        # Even with complex nested expressions in args, null target prevents evaluation
        null_node = self._make_null()
        # Complex nested arg that would fail if evaluated
        complex_arg = {
            "kind": "index",
            "span": {"start": 0, "end": 10},
            "target": self._make_number(42),  # not a list
            "index": self._make_number(0),
        }
        node = self._make_optional_call(null_node, [complex_arg])
        
        validate_ast(node)
        result = eval_expr(node)
        assert result is None

    def test_chain_of_null_calls(self):
        """Chain of ?() calls where first is null."""
        # null?(1)?(2) should return null at first call
        first = self._make_optional_call(self._make_null(), [self._make_number(1)])
        node = self._make_optional_call(first, [self._make_number(2)])
        
        validate_ast(node)
        result = eval_expr(node)
        # First call returns null, second call on null returns null
        assert result is None
