#!/usr/bin/env python3
"""Simple test runner for type predicates without pytest dependency."""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace/llm-native-lang')

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr

def run_tests():
    """Run all type predicate tests."""
    passed = 0
    failed = 0
    
    tests = [
        # is_int tests
        ("is_int(42)", True),
        ("is_int(0)", True),
        ("is_int(-5)", True),
        ("is_int(3.14)", False),
        ('is_int("hello")', False),
        ("is_int(true)", False),  # bool is NOT int
        ("is_int([1, 2])", False),
        ('is_int({"a": 1})', False),
        ("is_int(null)", False),
        
        # is_float tests
        ("is_float(3.14)", True),
        ("is_float(42)", False),
        ('is_float("3.14")', False),
        
        # is_string tests
        ('is_string("hello")', True),
        ('is_string("")', True),
        ("is_string(42)", False),
        ('is_string(["a", "b"])', False),
        
        # is_bool tests
        ("is_bool(true)", True),
        ("is_bool(false)", True),
        ("is_bool(1)", False),  # int is NOT bool
        ("is_bool(0)", False),
        ('is_bool("true")', False),
        
        # is_list tests
        ("is_list([1, 2, 3])", True),
        ("is_list([])", True),
        ("is_list([[1, 2], [3, 4]])", True),
        ('is_list("not a list")', False),
        ('is_list({"a": 1})', False),
        
        # is_object tests
        ('is_object({"a": 1})', True),
        ("is_object({})", True),
        ('is_object({"outer": {"inner": 42}})', True),
        ("is_object([1, 2])", False),
        ("is_object(null)", False),
        
        # is_null tests
        ("is_null(null)", True),
        ("is_null(0)", False),
        ("is_null(false)", False),
        ('is_null("")', False),
        ("is_null([])", False),
        
        # is_function tests
        ("is_function(fn(x) => x)", True),
        ("is_function(fn() => 42)", True),
        ("is_function(42)", False),
        ("is_function([1, 2, 3])", False),
        
        # Tests with variables
        ("let x = 5 in is_int(x)", True),
        ('let msg = "hello" in is_string(msg)', True),
        ("let xs = [1, 2] in is_list(xs)", True),
        ('let obj = {"a": 1} in is_object(obj)', True),
        
        # Tests with logical operators
        ("let x = 5 in is_int(x) and x > 0", True),
        ('is_string("hello") or is_list("hello")', True),
        ("let x = 10 in is_int(x) and x >= 0", True),
        ("let x = 5 in if is_int(x) then x + 1 else 0", 6),
        
        # Tests with expressions
        ("is_int(2 + 3)", True),
        ("is_list([1 + 1, 2 + 2])", True),
        ('is_object({"sum": 1 + 2})', True),
        ('is_string("hello" + " world")', True),
        
        # Negative path tests (should return False, not raise)
        ("is_int(fn() => 42)", False),
        ("is_function(null)", False),
        ('is_list({"a": 1})', False),
        ("is_object([1, 2])", False),
    ]
    
    for expr, expected in tests:
        try:
            node = parse_expr(expr)
            result = eval_expr(node)
            if result == expected:
                passed += 1
                print(f"  PASS: {expr}")
            else:
                failed += 1
                print(f"  FAIL: {expr}")
                print(f"    Expected: {expected}")
                print(f"    Got: {result}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {expr}")
            print(f"    Exception: {e}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
