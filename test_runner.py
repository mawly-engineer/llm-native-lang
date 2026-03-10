#!/usr/bin/env python3
"""Simple test runner for type predicate tests without pytest."""

import sys
from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append(f"FAIL: {name}\n  {error}")

results = TestResult()

def assert_eq(actual, expected, name):
    if actual == expected:
        results.add_pass()
        return True
    else:
        results.add_fail(name, f"Expected {expected}, got {actual}")
        return False

def run_test(name, test_func):
    try:
        test_func()
    except Exception as e:
        results.add_fail(name, str(e))

# TestIsInt
run_test("is_int(42)", lambda: assert_eq(eval_expr(parse_expr("is_int(42)")), True, "is_int positive int"))
run_test("is_int(0)", lambda: assert_eq(eval_expr(parse_expr("is_int(0)")), True, "is_int zero"))
run_test("is_int(-5)", lambda: assert_eq(eval_expr(parse_expr("is_int(-5)")), True, "is_int negative"))
run_test("is_int(3.14)", lambda: assert_eq(eval_expr(parse_expr("is_int(3.14)")), False, "is_int float"))
run_test("is_int('hello')", lambda: assert_eq(eval_expr(parse_expr('is_int("hello")')), False, "is_int string"))
run_test("is_int(true)", lambda: assert_eq(eval_expr(parse_expr("is_int(true)")), False, "is_int bool"))
run_test("is_int([1,2])", lambda: assert_eq(eval_expr(parse_expr("is_int([1, 2])")), False, "is_int list"))
run_test("is_int({a:1})", lambda: assert_eq(eval_expr(parse_expr('is_int({"a": 1})')), False, "is_int object"))
run_test("is_int(null)", lambda: assert_eq(eval_expr(parse_expr("is_int(null)")), False, "is_int null"))

# TestIsFloat
run_test("is_float(3.14)", lambda: assert_eq(eval_expr(parse_expr("is_float(3.14)")), True, "is_float float"))
run_test("is_float(42)", lambda: assert_eq(eval_expr(parse_expr("is_float(42)")), False, "is_float int"))
run_test("is_float('3.14')", lambda: assert_eq(eval_expr(parse_expr('is_float("3.14")')), False, "is_float string"))

# TestIsString
run_test("is_string('hello')", lambda: assert_eq(eval_expr(parse_expr('is_string("hello")')), True, "is_string string"))
run_test("is_string('')", lambda: assert_eq(eval_expr(parse_expr('is_string("")')), True, "is_string empty"))
run_test("is_string(42)", lambda: assert_eq(eval_expr(parse_expr("is_string(42)")), False, "is_string int"))
run_test("is_string([a,b])", lambda: assert_eq(eval_expr(parse_expr('is_string(["a", "b"])')), False, "is_string list"))

# TestIsBool
run_test("is_bool(true)", lambda: assert_eq(eval_expr(parse_expr("is_bool(true)")), True, "is_bool true"))
run_test("is_bool(false)", lambda: assert_eq(eval_expr(parse_expr("is_bool(false)")), True, "is_bool false"))
run_test("is_bool(1)", lambda: assert_eq(eval_expr(parse_expr("is_bool(1)")), False, "is_bool int 1"))
run_test("is_bool(0)", lambda: assert_eq(eval_expr(parse_expr("is_bool(0)")), False, "is_bool int 0"))
run_test("is_bool('true')", lambda: assert_eq(eval_expr(parse_expr('is_bool("true")')), False, "is_bool string"))

# TestIsList
run_test("is_list([1,2,3])", lambda: assert_eq(eval_expr(parse_expr("is_list([1, 2, 3])")), True, "is_list list"))
run_test("is_list([])", lambda: assert_eq(eval_expr(parse_expr("is_list([])")), True, "is_list empty"))
run_test("is_list(nested)", lambda: assert_eq(eval_expr(parse_expr("is_list([[1, 2], [3, 4]])")), True, "is_list nested"))
run_test("is_list('not list')", lambda: assert_eq(eval_expr(parse_expr('is_list("not a list")')), False, "is_list string"))
run_test("is_list({a:1})", lambda: assert_eq(eval_expr(parse_expr('is_list({"a": 1})')), False, "is_list object"))

# TestIsObject
run_test("is_object({a:1})", lambda: assert_eq(eval_expr(parse_expr('is_object({"a": 1})')), True, "is_object object"))
run_test("is_object({})", lambda: assert_eq(eval_expr(parse_expr("is_object({})")), True, "is_object empty"))
run_test("is_object(nested)", lambda: assert_eq(eval_expr(parse_expr('is_object({"outer": {"inner": 42}})')), True, "is_object nested"))
run_test("is_object([1,2])", lambda: assert_eq(eval_expr(parse_expr("is_object([1, 2])")), False, "is_object list"))
run_test("is_object(null)", lambda: assert_eq(eval_expr(parse_expr("is_object(null)")), False, "is_object null"))

# TestIsNull
run_test("is_null(null)", lambda: assert_eq(eval_expr(parse_expr("is_null(null)")), True, "is_null null"))
run_test("is_null(0)", lambda: assert_eq(eval_expr(parse_expr("is_null(0)")), False, "is_null zero"))
run_test("is_null(false)", lambda: assert_eq(eval_expr(parse_expr("is_null(false)")), False, "is_null false"))
run_test("is_null('')", lambda: assert_eq(eval_expr(parse_expr('is_null("")')), False, "is_null empty str"))
run_test("is_null([])", lambda: assert_eq(eval_expr(parse_expr("is_null([])")), False, "is_null empty list"))

# TestIsFunction
run_test("is_function(fn)", lambda: assert_eq(eval_expr(parse_expr("is_function(fn(x) => x)")), True, "is_function lambda"))
run_test("is_function(let f)", lambda: assert_eq(eval_expr(parse_expr("let f = fn(x) => x in is_function(f)")), True, "is_function let bound"))
run_test("is_function(no params)", lambda: assert_eq(eval_expr(parse_expr("is_function(fn() => 42)")), True, "is_function no params"))
run_test("is_function(42)", lambda: assert_eq(eval_expr(parse_expr("is_function(42)")), False, "is_function int"))
run_test("is_function(list)", lambda: assert_eq(eval_expr(parse_expr("is_function([1, 2, 3])")), False, "is_function list"))

# TestTypePredicatesWithVariables
run_test("is_int(var)", lambda: assert_eq(eval_expr(parse_expr("let x = 5 in is_int(x)")), True, "is_int var"))
run_test("is_string(var)", lambda: assert_eq(eval_expr(parse_expr('let msg = "hello" in is_string(msg)')), True, "is_string var"))
run_test("is_list(var)", lambda: assert_eq(eval_expr(parse_expr("let xs = [1, 2] in is_list(xs)")), True, "is_list var"))
run_test("is_object(var)", lambda: assert_eq(eval_expr(parse_expr('let obj = {"a": 1} in is_object(obj)')), True, "is_object var"))

# TestTypePredicatesWithLogicalOperators
run_test("is_int and comparison", lambda: assert_eq(eval_expr(parse_expr("let x = 5 in is_int(x) and x > 0")), True, "is_int and comparison"))
run_test("is_string or is_list", lambda: assert_eq(eval_expr(parse_expr('is_string("hello") or is_list("hello")')), True, "is_string or is_list"))
run_test("type guard", lambda: assert_eq(eval_expr(parse_expr("let x = 5 in if is_int(x) then x + 1 else 0")), 6, "type guard"))

# TestTypePredicatesWithExpressions
run_test("is_int arithmetic", lambda: assert_eq(eval_expr(parse_expr("is_int(2 + 3)")), True, "is_int arithmetic"))
run_test("is_list expr values", lambda: assert_eq(eval_expr(parse_expr("is_list([1 + 1, 2 + 2])")), True, "is_list expr"))
run_test("is_object expr values", lambda: assert_eq(eval_expr(parse_expr('is_object({"sum": 1 + 2})')), True, "is_object expr"))
run_test("is_string concat", lambda: assert_eq(eval_expr(parse_expr('is_string("hello" + " world")')), True, "is_string concat"))

# TestTypePredicatesNegativePaths
run_test("is_int with fn", lambda: assert_eq(eval_expr(parse_expr("is_int(fn() => 42)")), False, "is_int function"))
run_test("is_function null", lambda: assert_eq(eval_expr(parse_expr("is_function(null)")), False, "is_function null"))
run_test("is_list with obj", lambda: assert_eq(eval_expr(parse_expr('is_list({"a": 1})')), False, "is_list object"))
run_test("is_object with list", lambda: assert_eq(eval_expr(parse_expr("is_object([1, 2])")), False, "is_object list"))

print(f"\n{'='*50}")
print(f"Results: {results.passed} passed, {results.failed} failed")
print(f"{'='*50}")

if results.errors:
    print("\nErrors:")
    for err in results.errors:
        print(err)
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
