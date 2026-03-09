"""Manual tests for string escape sequence parsing (LNG-CORE-45)."""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace/llm-native-lang/runtime')

from grammar_contract import parse_expr, ParseError

tests_passed = 0
tests_failed = 0

def assert_eq(actual, expected, name):
    global tests_passed, tests_failed
    if actual == expected:
        print(f"  ✓ {name}")
        tests_passed += 1
    else:
        print(f"  ✗ {name}")
        print(f"    Expected: {expected!r}")
        print(f"    Actual: {actual!r}")
        tests_failed += 1

def expect_exception(source, expected_code, name):
    global tests_passed, tests_failed
    try:
        parse_expr(source)
        print(f"  ✗ {name} - Expected exception {expected_code}, got success")
        tests_failed += 1
    except ParseError as e:
        if e.code == expected_code:
            print(f"  ✓ {name}")
            tests_passed += 1
        else:
            print(f"  ✗ {name} - Wrong code: {e.code} != {expected_code}")
            tests_failed += 1

print("\n=== POSITIVE PATH: Valid Escape Sequences ===")

# Test: newline escape
result = parse_expr('"hello\\nworld"')
assert_eq(result["kind"], "string", "parse_expr returns string node for \\n")
assert_eq(result["value"], "hello\nworld", "\\n converts to newline")

# Test: tab escape
result = parse_expr('"tab\\there"')
assert_eq(result["kind"], "string", "parse_expr returns string node for \\t")
assert_eq(result["value"], "tab\there", "\\t converts to tab")

# Test: carriage return escape
result = parse_expr('"line1\\rline2"')
assert_eq(result["kind"], "string", "parse_expr returns string node for \\r")
assert_eq(result["value"], "line1\rline2", "\\r converts to carriage return")

# Test: escaped quote
result = parse_expr('"say \\\"hello\\\""')
assert_eq(result["kind"], "string", "parse_expr returns string node for escaped quote")
assert_eq(result["value"], 'say "hello"', "escaped quote allows quote in string")

# Test: escaped backslash
result = parse_expr('"path\\\\to\\\\file"')
assert_eq(result["kind"], "string", "parse_expr returns string node for escaped backslash")
assert_eq(result["value"], "path\\to\\file", "\\\\ converts to single backslash")

# Test: multiple escapes
result = parse_expr('"line1\\nline2\\ttab\\n\\"quoted\\""')
assert_eq(result["value"], 'line1\nline2\ttab\n"quoted"', "multiple escape types work together")

# Test: plain string (no escapes)
result = parse_expr('"hello world"')
assert_eq(result["value"], "hello world", "plain string without escapes")

print("\n=== NEGATIVE PATH: Invalid Escape Sequences ===")

# Invalid escape: \x
expect_exception('"hello\\xworld"', "E_PARSE_INVALID_ESCAPE", "\\x raises E_PARSE_INVALID_ESCAPE")

# Invalid escape: \q
expect_exception('"hello\\qworld"', "E_PARSE_INVALID_ESCAPE", "\\q raises E_PARSE_INVALID_ESCAPE")

# Invalid escape: \0
expect_exception('"hello\\0world"', "E_PARSE_INVALID_ESCAPE", "\\0 raises E_PARSE_INVALID_ESCAPE")

# Unterminated string
expect_exception('"hello world', "E_PARSE_UNTERMINATED_STRING", "unterminated string raises error")

# String ending with backslash
try:
    parse_expr('"hello\\"')
    print("  ✗ String ending with backslash - expected exception")
    tests_failed += 1
except ParseError as e:
    if e.code == "E_PARSE_UNTERMINATED_STRING":
        print("  ✓ String ending with backslash raises E_PARSE_UNTERMINATED_STRING")
        tests_passed += 1
    else:
        print(f"  ✗ String ending with backslash - wrong code: {e.code}")
        tests_failed += 1

print("\n=== LOCATION METADATA ===")

try:
    parse_expr('"hello\\z"')
    print("  ✗ Error location - expected exception")
    tests_failed += 1
except ParseError as e:
    has_location = "line" in e.location and "column" in e.location
    if has_location:
        print(f"  ✓ ParseError includes location metadata: {e.location}")
        tests_passed += 1
    else:
        print(f"  ✗ ParseError missing location metadata: {e.location}")
        tests_failed += 1

print("\n=== EXPRESSION INTEGRATION ===")

# Escaped string in concatenation
result = parse_expr('"hello\\n" + "world"')
assert_eq(result["kind"], "concat_bin", "escaped string in concatenation")

# Escaped string in list
result = parse_expr('["a\\nb", "c\\td"]')
assert_eq(result["kind"], "list", "escaped string in list literal")

# Escaped string in object
result = parse_expr('{"key": "val\\nue"}')
assert_eq(result["kind"], "object", "escaped string in object literal")

print("\n=== SUMMARY ===")
print(f"Passed: {tests_passed}")
print(f"Failed: {tests_failed}")

if tests_failed > 0:
    sys.exit(1)
else:
    print("\n✓ All tests passed!")
