"""Tests for recursive let bindings (let rec) with fixpoint semantics."""

import unittest

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError


class RecursiveLetTests(unittest.TestCase):
    """Test suite for recursive let bindings (let rec)."""

    # === Grammar tests ===

    def test_parse_recursive_let(self):
        """Parse 'let rec' expression creates let node with recursive=True."""
        node = parse_expr('let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(5)')
        self.assertEqual(node["kind"], "let")
        self.assertEqual(node["name"], "fact")
        self.assertEqual(node.get("recursive"), True)

    def test_parse_recursive_let_without_rec(self):
        """Parse 'let' without 'rec' creates let node with recursive=False."""
        node = parse_expr('let x = 1 in x + 1')
        self.assertEqual(node["kind"], "let")
        self.assertEqual(node["name"], "x")
        self.assertIn(node.get("recursive", False), [False, None])

    # === Factorial tests ===

    def test_recursive_factorial_5(self):
        """eval('let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(5)') returns 120."""
        result = eval_expr(parse_expr(
            'let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(5)'
        ))
        self.assertEqual(result, 120)

    def test_recursive_factorial_0(self):
        """Factorial of 0 should return 1 (base case)."""
        result = eval_expr(parse_expr(
            'let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(0)'
        ))
        self.assertEqual(result, 1)

    def test_recursive_factorial_1(self):
        """Factorial of 1 should return 1 (base case)."""
        result = eval_expr(parse_expr(
            'let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(1)'
        ))
        self.assertEqual(result, 1)

    # === Fibonacci tests ===

    def test_recursive_fibonacci_10(self):
        """eval('let rec fib = fn(n) => if n <= 1 then n else fib(n-1) + fib(n-2) in fib(10)') returns 55."""
        result = eval_expr(parse_expr(
            'let rec fib = fn(n) => if n <= 1 then n else fib(n-1) + fib(n-2) in fib(10)'
        ))
        self.assertEqual(result, 55)

    def test_recursive_fibonacci_0(self):
        """Fibonacci of 0 should return 0."""
        result = eval_expr(parse_expr(
            'let rec fib = fn(n) => if n <= 1 then n else fib(n-1) + fib(n-2) in fib(0)'
        ))
        self.assertEqual(result, 0)

    def test_recursive_fibonacci_1(self):
        """Fibonacci of 1 should return 1."""
        result = eval_expr(parse_expr(
            'let rec fib = fn(n) => if n <= 1 then n else fib(n-1) + fib(n-2) in fib(1)'
        ))
        self.assertEqual(result, 1)

    # === Arithmetic recursion tests ===

    def test_recursive_countdown_sum(self):
        """Sum from n down to 0 using recursion."""
        result = eval_expr(parse_expr(
            'let rec sum_to = fn(n) => if n == 0 then 0 else n + sum_to(n - 1) in sum_to(10)'
        ))
        self.assertEqual(result, 55)  # 10+9+8+...+1 = 55

    def test_recursive_power(self):
        """Power function using recursion (x^n)."""
        result = eval_expr(parse_expr(
            'let rec power = fn(x, n) => if n == 0 then 1 else x * power(x, n - 1) in power(2, 10)'
        ))
        self.assertEqual(result, 1024)

    def test_recursive_gcd(self):
        """GCD using Euclid's algorithm with recursion."""
        result = eval_expr(parse_expr(
            'let rec gcd = fn(a, b) => if b == 0 then a else gcd(b, a - (a // b) * b) in gcd(48, 18)'
        ))
        self.assertEqual(result, 6)

    # === Nested recursive functions ===

    def test_nested_recursive_in_let(self):
        """Recursive function inside non-recursive let."""
        result = eval_expr(parse_expr(
            'let x = 5 in let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in fact(x)'
        ))
        self.assertEqual(result, 120)

    def test_recursive_function_as_argument(self):
        """Recursive function passed as argument to higher-order function."""
        result = eval_expr(parse_expr(
            'let rec double = fn(n) => if n == 0 then 0 else 2 + double(n - 1) '
            'in let apply = fn(f, x) => f(x) '
            'in apply(double, 5)'
        ))
        self.assertEqual(result, 10)

    # === Higher-order recursive functions ===

    def test_recursive_closure(self):
        """Recursive function capturing closure."""
        result = eval_expr(parse_expr(
            'let multiplier = 3 in '
            'let rec times = fn(n) => if n == 0 then 0 else multiplier + times(n - 1) '
            'in times(4)'
        ))
        self.assertEqual(result, 12)

    # === Negative tests ===

    def test_non_function_recursive_binding(self):
        """Recursive binding on non-function should still work for values."""
        result = eval_expr(parse_expr(
            'let rec x = 42 in x'
        ))
        self.assertEqual(result, 42)

    def test_recursive_fuel_exhaustion(self):
        """Infinite recursion should hit fuel limit."""
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr(
                'let rec loop = fn(n) => loop(n + 1) in loop(0)'
            ), fuel_limit=100)
        self.assertEqual(ctx.exception.code, "E_RT_FUEL_EXHAUSTED")

    def test_recursive_arity_mismatch(self):
        """Calling recursive function with wrong arity should raise E_RT_ARITY_MISMATCH."""
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr(
                'let rec add = fn(a, b) => a + b in add(1)'
            ))
        self.assertEqual(ctx.exception.code, "E_RT_ARITY_MISMATCH")

    # === Shadowing and scope tests ===

    def test_recursive_shadowing(self):
        """Recursive function can be shadowed by inner let."""
        result = eval_expr(parse_expr(
            'let rec fact = fn(n) => if n <= 1 then 1 else n * fact(n - 1) in '
            'let fact = fn(n) => n * n in fact(5)'
        ))
        # Shadowed with non-recursive square function
        self.assertEqual(result, 25)


if __name__ == "__main__":
    unittest.main()
