#!/usr/bin/env python3
"""Simple test runner for comparison operators without pytest dependency."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError

def run_tests(name, tests, error_tests=None):
    """Run a suite of tests."""
    print(f"\nTesting {name}...")
    passed = 0
    failed = 0

    for expr, expected in tests:
        try:
            node = parse_expr(expr)
            result = eval_expr(node)
            if result == expected:
                passed += 1
            else:
                failed += 1
                print(f"  FAIL: {expr} = {result}, expected {expected}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {expr} raised {e}")

    if error_tests:
        for expr, expected_code in error_tests:
            try:
                node = parse_expr(expr)
                result = eval_expr(node)
                failed += 1
                print(f"  FAIL: {expr} should raise {expected_code}, got {result}")
            except EvalError as e:
                if e.code == expected_code:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL: {expr} raised {e.code}, expected {expected_code}")
            except Exception as e:
                failed += 1
                print(f"  FAIL: {expr} raised unexpected {type(e).__name__}: {e}")

    print(f"  {name}: {passed} passed, {failed} failed")
    return passed, failed

if __name__ == "__main__":
    print("=" * 60)
    print("Comparison Operators Test Runner")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    # Numeric comparisons
    p, f = run_tests("numeric comparisons", [
        ("5 < 10", True),
        ("10 < 5", False),
        ("10 <= 10", True),
        ("10 <= 5", False),
        ("15 > 10", True),
        ("5 > 10", False),
        ("10 >= 10", True),
        ("5 >= 10", False),
        ("3.14 < 3.15", True),
        ("3.15 < 3.14", False),
        ("5 < 5.5", True),
        ("5.5 > 5", True),
    ])
    total_passed += p
    total_failed += f

    # String comparisons
    p, f = run_tests("string comparisons", [
        ('"abc" < "def"', True),
        ('"def" < "abc"', False),
        ('"abc" <= "abc"', True),
        ('"xyz" > "abc"', True),
        ('"hello" >= "hello"', True),
        ('"" < "a"', True),
    ])
    total_passed += p
    total_failed += f

    # Equality comparisons
    p, f = run_tests("equality comparisons", [
        ("5 == 5", True),
        ("5 == 10", False),
        ("5 != 10", True),
        ("5 != 5", False),
        ('"hello" == "hello"', True),
        ('"hello" == "world"', False),
        ('"hello" != "world"', True),
        ("true == true", True),
        ("true == false", False),
        ("null == null", True),
    ])
    total_passed += p
    total_failed += f

    # Integration with if/logical operators
    p, f = run_tests("integration with if/logical operators", [
        ("if 5 > 3 then 1 else 0", 1),
        ("if 3 > 5 then 1 else 0", 0),
        ("(5 > 3) and (10 < 20)", True),
        ("(5 > 10) or (3 < 7)", True),
        ("let x = 10 in x > 5", True),
        ("let a = 5 in let b = 10 in a < b and b > a", True),
    ])
    total_passed += p
    total_failed += f

    # Edge cases
    p, f = run_tests("edge cases", [
        ("0 < 1", True),
        ("-10 < -5", True),
        ("-5 < 5", True),
        ("5 <= 5", True),
        ("5 >= 5", True),
        ("1000000 > 999999", True),
    ])
    total_passed += p
    total_failed += f

    # Negative paths - type errors
    p, f = run_tests("negative paths (type errors)", [], [
        ('5 < "hello"', "E_RT_TYPE"),
        ('"hello" > 5', "E_RT_TYPE"),
        ("true < false", "E_RT_TYPE"),
        ("true > false", "E_RT_TYPE"),
        ("null < 5", "E_RT_TYPE"),
        ('5 == "5"', "E_RT_TYPE"),
        ("null != 5", "E_RT_TYPE"),
    ])
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print("=" * 60)

    sys.exit(0 if total_failed == 0 else 1)
