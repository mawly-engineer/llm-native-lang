#!/usr/bin/env python3
"""Run escape sequence tests."""
from grammar_contract import parse_expr, ParseError

def test_escape_newline():
    result = parse_expr(r'"hello\nworld"')
    assert result["kind"] == "string"
    assert result["value"] == "hello\nworld", f"Got {repr(result['value'])}"
    print("✓ newline escape")

def test_escape_tab():
    result = parse_expr(r'"tab\there"')
    assert result["value"] == "tab\there", f"Got {repr(result['value'])}"
    print("✓ tab escape")

def test_escape_carriage_return():
    result = parse_expr(r'"line1\rline2"')
    assert result["value"] == "line1\rline2", f"Got {repr(result['value'])}"
    print("✓ carriage return escape")

def test_escape_quote():
    result = parse_expr(r'"say \"hello\""')
    assert result["value"] == 'say "hello"', f"Got {repr(result['value'])}"
    print("✓ quote escape")

def test_escape_backslash():
    result = parse_expr(r'"path\\to\\file"')
    assert result["value"] == "path\\to\\file", f"Got {repr(result['value'])}"
    print("✓ backslash escape")

def test_multiple_escapes():
    result = parse_expr(r'"line1\nline2\ttab\n\"quoted\""')
    expected = 'line1\nline2\ttab\n"quoted"'
    assert result["value"] == expected, f"Got {repr(result['value'])}"
    print("✓ multiple escapes")

def test_plain_string():
    result = parse_expr('"hello world"')
    assert result["value"] == "hello world"
    print("✓ plain string")

def test_invalid_escape():
    try:
        parse_expr(r'"hello\xworld"')
        print("✗ Expected E_PARSE_INVALID_ESCAPE")
        return False
    except ParseError as e:
        if e.code == "E_PARSE_INVALID_ESCAPE" and e.location.get("escape_char") == "x":
            print("✓ invalid escape (\\x)")
            return True
        print(f"✗ Wrong error: {e.code}, {e.location}")
        return False

def test_unterminated_string():
    try:
        parse_expr('"hello world')
        print("✗ Expected E_PARSE_UNTERMINATED_STRING")
        return False
    except ParseError as e:
        if e.code == "E_PARSE_UNTERMINATED_STRING":
            print("✓ unterminated string")
            return True
        print(f"✗ Wrong error: {e.code}")
        return False

def test_unterminated_escape():
    try:
        parse_expr(r'"hello\"')
        print("✗ Expected E_PARSE_UNTERMINATED_STRING")
        return False
    except ParseError as e:
        if e.code == "E_PARSE_UNTERMINATED_STRING":
            print("✓ unterminated escape")
            return True
        print(f"✗ Wrong error: {e.code}")
        return False

def test_escape_in_concat():
    result = parse_expr(r'"hello\n" + "world"')
    assert result["kind"] == "concat_bin"
    print("✓ escape in concat")

def test_escape_in_list():
    result = parse_expr(r'["a\nb", "c\td"]')
    assert result["kind"] == "list"
    assert result["items"][0]["value"] == "a\nb"
    assert result["items"][1]["value"] == "c\td"
    print("✓ escape in list")

def test_escape_in_object():
    result = parse_expr(r'{"key": "val\nue"}')
    assert result["kind"] == "object"
    assert result["entries"][0]["value"]["value"] == "val\nue"
    print("✓ escape in object")

if __name__ == "__main__":
    print("=== String Escape Sequence Tests ===\n")

    print("--- Positive Path ---")
    test_escape_newline()
    test_escape_tab()
    test_escape_carriage_return()
    test_escape_quote()
    test_escape_backslash()
    test_multiple_escapes()
    test_plain_string()

    print("\n--- Negative Path ---")
    test_invalid_escape()
    test_unterminated_string()
    test_unterminated_escape()

    print("\n--- Expression Context ---")
    test_escape_in_concat()
    test_escape_in_list()
    test_escape_in_object()

    print("\n✅ ALL TESTS PASSED!")
