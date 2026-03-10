#!/usr/bin/env python3
"""Simple test runner for llm-native-lang tests without pytest dependency."""

import sys
import os
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError

def test_type_predicates():
    """Test type predicates."""
    print("Testing type predicates...")
    tests_passed = 0
    tests_failed = 0

    # is_int tests
    tests = [
        ("is_int(42)", True),
        ("is_int(0)", True),
        ("is_int(-5)", True),
        ("is_int(3.14)", False),
        ("is_int('hello')", False),
        ("is_int(true)", False),
        ("is_int(false)", False),
        ("is_int([1,2])", False),
        ("is_int({})", False),
        ("is_int(null)", False),
        ("is_float(3.14)", True),
        ("is_float(42)", False),
        ("is_string('hello')", True),
        ("is_string(42)", False),
        ("is_bool(true)", True),
        ("is_bool(false)", True),
        ("is_bool(1)", False),
        ("is_list([1,2])", True),
        ("is_list({})", False),
        ("is_object({a:1})", True),
        ("is_object([1,2])", False),
        ("is_null(null)", True),
        ("is_null(0)", False),
    ]

    for expr, expected in tests:
        try:
            node = parse_expr(expr)
            result = eval_expr(node)
            if result == expected:
                tests_passed += 1
            else:
                tests_failed += 1
                print(f"  FAIL: {expr} = {result}, expected {expected}")
        except Exception as e:
            tests_failed += 1
            print(f"  FAIL: {expr} raised {e}")

    print(f"  Type predicates: {tests_passed} passed, {tests_failed} failed")
    return tests_passed, tests_failed

def test_logical_operators():
    """Test logical operators."""
    print("\nTesting logical operators...")
    tests_passed = 0
    tests_failed = 0

    tests = [
        ("true and true", True),
        ("true and false", False),
        ("false and true", False),
        ("false and false", False),
        ("true or true", True),
        ("true or false", True),
        ("false or true", True),
        ("false or false", False),
        ("true and true and true", True),
        ("true and true and false", False),
        ("true or false or false", True),
        ("false or false or false", False),
    ]

    for expr, expected in tests:
        try:
            node = parse_expr(expr)
            result = eval_expr(node)
            if result == expected:
                tests_passed += 1
            else:
                tests_failed += 1
                print(f"  FAIL: {expr} = {result}, expected {expected}")
        except Exception as e:
            tests_failed += 1
            print(f"  FAIL: {expr} raised {e}")

    print(f"  Logical operators: {tests_passed} passed, {tests_failed} failed")
    return tests_passed, tests_failed

if __name__ == "__main__":
    print("=" * 60)
    print("Simple Test Runner")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    p, f = test_type_predicates()
    total_passed += p
    total_failed += f

    p, f = test_logical_operators()
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print("=" * 60)

    sys.exit(0 if total_failed == 0 else 1)
