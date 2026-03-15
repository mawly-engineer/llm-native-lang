"""Tests for range expression evaluation."""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


class TestRangeSingleArgument(unittest.TestCase):
    """Tests for range(end) form."""

    def test_range_5(self):
        """range(5) should return [0, 1, 2, 3, 4]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 7},
            "args": [{"kind": "number", "span": {"start": 6, "end": 7}, "value": 5}]
        }
        result = eval_expr(node)
        self.assertEqual(result, [0, 1, 2, 3, 4])

    def test_range_0(self):
        """range(0) should return empty list."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 7},
            "args": [{"kind": "number", "span": {"start": 6, "end": 7}, "value": 0}]
        }
        result = eval_expr(node)
        self.assertEqual(result, [])

    def test_range_negative_end(self):
        """range(-3) should return empty list (start=0 > end=-3)."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 8},
            "args": [{"kind": "number", "span": {"start": 6, "end": 8}, "value": -3}]
        }
        result = eval_expr(node)
        self.assertEqual(result, [])


class TestRangeTwoArguments(unittest.TestCase):
    """Tests for range(start, end) form."""

    def test_range_1_to_5(self):
        """range(1, 5) should return [1, 2, 3, 4]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 10},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 1},
                {"kind": "number", "span": {"start": 9, "end": 10}, "value": 5}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [1, 2, 3, 4])

    def test_range_equal_start_end(self):
        """range(5, 5) should return empty list."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 10},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 5},
                {"kind": "number", "span": {"start": 9, "end": 10}, "value": 5}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [])

    def test_range_negative_start(self):
        """range(-2, 3) should return [-2, -1, 0, 1, 2]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 11},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 8}, "value": -2},
                {"kind": "number", "span": {"start": 10, "end": 11}, "value": 3}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [-2, -1, 0, 1, 2])

    def test_range_negative_end(self):
        """range(-5, -2) should return [-5, -4, -3]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 12},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 8}, "value": -5},
                {"kind": "number", "span": {"start": 10, "end": 12}, "value": -2}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [-5, -4, -3])


class TestRangeThreeArguments(unittest.TestCase):
    """Tests for range(start, end, step) form."""

    def test_range_with_step_2(self):
        """range(0, 10, 2) should return [0, 2, 4, 6, 8]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 14},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 0},
                {"kind": "number", "span": {"start": 9, "end": 11}, "value": 10},
                {"kind": "number", "span": {"start": 13, "end": 14}, "value": 2}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_range_with_negative_step(self):
        """range(5, 0, -1) should return [5, 4, 3, 2, 1]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 15},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 5},
                {"kind": "number", "span": {"start": 9, "end": 10}, "value": 0},
                {"kind": "number", "span": {"start": 12, "end": 14}, "value": -1}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [5, 4, 3, 2, 1])

    def test_range_negative_step_overshoot(self):
        """range(5, -3, -2) should return [5, 3, 1, -1]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 16},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 5},
                {"kind": "number", "span": {"start": 9, "end": 11}, "value": -3},
                {"kind": "number", "span": {"start": 13, "end": 15}, "value": -2}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [5, 3, 1, -1])

    def test_range_step_larger_than_range(self):
        """range(0, 5, 10) should return [0]."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 14},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 0},
                {"kind": "number", "span": {"start": 9, "end": 10}, "value": 5},
                {"kind": "number", "span": {"start": 12, "end": 14}, "value": 10}
            ]
        }
        result = eval_expr(node)
        self.assertEqual(result, [0])


class TestRangeErrorCases(unittest.TestCase):
    """Tests for range error handling."""

    def test_range_step_zero(self):
        """range(0, 5, 0) should raise E_RT_RANGE_STEP_ZERO."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 14},
            "args": [
                {"kind": "number", "span": {"start": 6, "end": 7}, "value": 0},
                {"kind": "number", "span": {"start": 9, "end": 10}, "value": 5},
                {"kind": "number", "span": {"start": 12, "end": 13}, "value": 0}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(node)
        self.assertEqual(ctx.exception.code, "E_RT_RANGE_STEP_ZERO")

    def test_range_non_int_argument(self):
        """range("a") should raise E_RT_TYPE."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 9},
            "args": [{"kind": "string", "span": {"start": 6, "end": 9}, "value": "a"}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(node)
        self.assertEqual(ctx.exception.code, "E_RT_TYPE")


class TestRangeWithVariables(unittest.TestCase):
    """Tests for range with variable arguments."""

    def test_range_with_variables(self):
        """range(x, y, z) should work with variable values."""
        node = {
            "kind": "range_call",
            "span": {"start": 0, "end": 14},
            "args": [
                {"kind": "ident", "span": {"start": 6, "end": 7}, "name": "x"},
                {"kind": "ident", "span": {"start": 9, "end": 10}, "name": "y"},
                {"kind": "ident", "span": {"start": 12, "end": 13}, "name": "z"}
            ]
        }
        result = eval_expr(node, env={"x": 1, "y": 10, "z": 3})
        self.assertEqual(result, [1, 4, 7])


if __name__ == "__main__":
    unittest.main()
