"""Tests for string escape sequence parsing (LNG-CORE-45)."""

import pytest
from grammar_contract import parse_expr, ParseError


class TestStringEscapeSequences:
    """Positive path: valid escape sequences parse correctly."""

    def test_escape_newline(self):
        """\n converts to newline character."""
        result = parse_expr('"hello\\nworld"')
        assert result["kind"] == "string"
        assert result["value"] == "hello\nworld"

    def test_escape_tab(self):
        """\t converts to tab character."""
        result = parse_expr('"tab\\there"')
        assert result["kind"] == "string"
        assert result["value"] == "tab\there"

    def test_escape_carriage_return(self):
        """\r converts to carriage return."""
        result = parse_expr('"line1\\rline2"')
        assert result["kind"] == "string"
        assert result["value"] == "line1\rline2"

    def test_escape_quote(self):
        """\" allows quote inside string."""
        result = parse_expr('"say \\\"hello\\\""')
        assert result["kind"] == "string"
        assert result["value"] == 'say "hello"'

    def test_escape_backslash(self):
        """\\ converts to single backslash."""
        result = parse_expr('"path\\\\to\\\\file"')
        assert result["kind"] == "string"
        assert result["value"] == "path\\to\\file"

    def test_multiple_escapes(self):
        """Multiple escape types in one string."""
        result = parse_expr('"line1\\nline2\\ttab\\n\\"quoted\\""')
        assert result["kind"] == "string"
        assert result["value"] == 'line1\nline2\ttab\n"quoted"'

    def test_no_escapes(self):
        """Plain string without escapes works."""
        result = parse_expr('"hello world"')
        assert result["kind"] == "string"
        assert result["value"] == "hello world"


class TestStringEscapeNegativePath:
    """Negative path: invalid escape sequences raise structured errors."""

    def test_invalid_escape_x(self):
        """\x raises E_PARSE_INVALID_ESCAPE."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello\\xworld"')
        assert exc_info.value.code == "E_PARSE_INVALID_ESCAPE"
        assert exc_info.value.location["escape_char"] == "x"

    def test_invalid_escape_q(self):
        """\q raises E_PARSE_INVALID_ESCAPE."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello\\qworld"')
        assert exc_info.value.code == "E_PARSE_INVALID_ESCAPE"
        assert exc_info.value.location["escape_char"] == "q"

    def test_invalid_escape_digit(self):
        """\0 raises E_PARSE_INVALID_ESCAPE."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello\\0world"')
        assert exc_info.value.code == "E_PARSE_INVALID_ESCAPE"
        assert exc_info.value.location["escape_char"] == "0"

    def test_unterminated_string(self):
        """Unterminated string raises E_PARSE_UNTERMINATED_STRING."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello world')
        assert exc_info.value.code == "E_PARSE_UNTERMINATED_STRING"

    def test_unterminated_escape_at_end(self):
        """String ending with backslash raises E_PARSE_UNTERMINATED_STRING."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello\\"')
        assert exc_info.value.code == "E_PARSE_UNTERMINATED_STRING"

    def test_error_includes_location(self):
        """Parse errors include line and column."""
        with pytest.raises(ParseError) as exc_info:
            parse_expr('"hello\\z"')
        assert "line" in exc_info.value.location
        assert "column" in exc_info.value.location


class TestStringEscapeInExpressions:
    """Escape sequences work correctly in larger expressions."""

    def test_escape_in_concat(self):
        """Escaped string in concatenation."""
        result = parse_expr('"hello\\n" + "world"')
        assert result["kind"] == "concat_bin"

    def test_escape_in_list(self):
        """Escaped string in list literal."""
        result = parse_expr('["a\\nb", "c\\td"]')
        assert result["kind"] == "list"

    def test_escape_in_object(self):
        """Escaped string in object literal."""
        result = parse_expr('{"key": "val\\nue"}')
        assert result["kind"] == "object"
