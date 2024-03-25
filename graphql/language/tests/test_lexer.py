from pytest import raises

from graphql.error import GraphQLSyntaxError
from graphql.language.lexer import Lexer, Token, TokenKind
from graphql.language.source import Source


def lex_one(s):
    # type: (str) -> Token
    return Lexer(Source(s)).next_token()


def test_repr_token():
    # type: () -> None
    token = lex_one("500")
    assert repr(token) == "<Token kind=Int at 0..3 value='500'>"


def test_disallows_uncommon_control_characters():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("\u0007")

    assert (
        'Syntax Error GraphQL (1:1) Invalid character "\\u0007"'
        in excinfo.value.message
    )


def test_accepts_bom_header():
    # type: () -> None
    assert lex_one("\uFEFF foo") == Token(TokenKind.NAME, 2, 5, "foo")


def test_skips_whitespace():
    # type: () -> None
    assert (
        lex_one(
            """

    foo


"""
        )
        == Token(TokenKind.NAME, 6, 9, "foo")
    )

    assert (
        lex_one(
            """
    #comment
    foo#comment
"""
        )
        == Token(TokenKind.NAME, 18, 21, "foo")
    )

    assert lex_one(""",,,foo,,,""") == Token(TokenKind.NAME, 3, 6, "foo")


def test_errors_respect_whitespace():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(
            """

    ?


"""
        )
    assert excinfo.value.message == (
        'Syntax Error GraphQL (3:5) Unexpected character "?".\n'
        "\n"
        "2: \n"
        "3:     ?\n"
        "       ^\n"
        "4: \n"
    )


def test_lexes_strings():
    # type: () -> None
    assert lex_one('"simple"') == Token(TokenKind.STRING, 0, 8, "simple")
    assert lex_one('" white space "') == Token(TokenKind.STRING, 0, 15, " white space ")
    assert lex_one('"quote \\""') == Token(TokenKind.STRING, 0, 10, 'quote "')
    assert lex_one('"escaped \\n\\r\\b\\t\\f"') == Token(
        TokenKind.STRING, 0, 20, "escaped \n\r\b\t\f"
    )
    assert lex_one('"slashes \\\\ \\/"') == Token(
        TokenKind.STRING, 0, 15, "slashes \\ /"
    )
    assert lex_one('"unicode \\u1234\\u5678\\u90AB\\uCDEF"') == Token(
        TokenKind.STRING, 0, 34, "unicode \u1234\u5678\u90AB\uCDEF"
    )


def test_lex_reports_useful_string_errors():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"')
    assert "Syntax Error GraphQL (1:2) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"no end quote')
    assert "Syntax Error GraphQL (1:14) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"contains unescaped \u0007 control char"')
    assert (
        'Syntax Error GraphQL (1:21) Invalid character within String: "\\u0007".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"null-byte is not \u0000 end of file"')
    assert (
        'Syntax Error GraphQL (1:19) Invalid character within String: "\\u0000".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"multi\nline"')
    assert "Syntax Error GraphQL (1:7) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"multi\rline"')
    assert "Syntax Error GraphQL (1:7) Unterminated string" in excinfo.value.message

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\z esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\z."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\x esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\x."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\u1 esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\u1 es."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\u0XX1 esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\u0XX1."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\uXXXX esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uXXXX"
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\uFXXX esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uFXXX."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one('"bad \\uXXXF esc"')
    assert (
        "Syntax Error GraphQL (1:7) Invalid character escape sequence: \\uXXXF."
        in excinfo.value.message
    )


def test_lexes_numbers():
    # type: () -> None
    assert lex_one("4") == Token(TokenKind.INT, 0, 1, "4")
    assert lex_one("4.123") == Token(TokenKind.FLOAT, 0, 5, "4.123")
    assert lex_one("-4") == Token(TokenKind.INT, 0, 2, "-4")
    assert lex_one("9") == Token(TokenKind.INT, 0, 1, "9")
    assert lex_one("0") == Token(TokenKind.INT, 0, 1, "0")
    assert lex_one("-4.123") == Token(TokenKind.FLOAT, 0, 6, "-4.123")
    assert lex_one("0.123") == Token(TokenKind.FLOAT, 0, 5, "0.123")
    assert lex_one("123e4") == Token(TokenKind.FLOAT, 0, 5, "123e4")
    assert lex_one("123E4") == Token(TokenKind.FLOAT, 0, 5, "123E4")
    assert lex_one("123e-4") == Token(TokenKind.FLOAT, 0, 6, "123e-4")
    assert lex_one("123e+4") == Token(TokenKind.FLOAT, 0, 6, "123e+4")
    assert lex_one("-1.123e4") == Token(TokenKind.FLOAT, 0, 8, "-1.123e4")
    assert lex_one("-1.123E4") == Token(TokenKind.FLOAT, 0, 8, "-1.123E4")
    assert lex_one("-1.123e-4") == Token(TokenKind.FLOAT, 0, 9, "-1.123e-4")
    assert lex_one("-1.123e+4") == Token(TokenKind.FLOAT, 0, 9, "-1.123e+4")
    assert lex_one("-1.123e4567") == Token(TokenKind.FLOAT, 0, 11, "-1.123e4567")


def test_lex_reports_useful_number_errors():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("00")
    assert (
        'Syntax Error GraphQL (1:2) Invalid number, unexpected digit after 0: "0".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("+1")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character "+"' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("1.")
    assert (
        "Syntax Error GraphQL (1:3) Invalid number, expected digit but got: <EOF>."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one(".123")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character ".".' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("1.A")
    assert (
        'Syntax Error GraphQL (1:3) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("-A")
    assert (
        'Syntax Error GraphQL (1:2) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("1.0e")
    assert (
        "Syntax Error GraphQL (1:5) Invalid number, expected digit but got: <EOF>."
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("1.0eA")
    assert (
        'Syntax Error GraphQL (1:5) Invalid number, expected digit but got: "A".'
        in excinfo.value.message
    )


def test_lexes_punctuation():
    # type: () -> None
    assert lex_one("!") == Token(TokenKind.BANG, 0, 1)
    assert lex_one("$") == Token(TokenKind.DOLLAR, 0, 1)
    assert lex_one("(") == Token(TokenKind.PAREN_L, 0, 1)
    assert lex_one(")") == Token(TokenKind.PAREN_R, 0, 1)
    assert lex_one("...") == Token(TokenKind.SPREAD, 0, 3)
    assert lex_one(":") == Token(TokenKind.COLON, 0, 1)
    assert lex_one("=") == Token(TokenKind.EQUALS, 0, 1)
    assert lex_one("@") == Token(TokenKind.AT, 0, 1)
    assert lex_one("[") == Token(TokenKind.BRACKET_L, 0, 1)
    assert lex_one("]") == Token(TokenKind.BRACKET_R, 0, 1)
    assert lex_one("{") == Token(TokenKind.BRACE_L, 0, 1)
    assert lex_one("|") == Token(TokenKind.PIPE, 0, 1)
    assert lex_one("}") == Token(TokenKind.BRACE_R, 0, 1)


def test_lex_reports_useful_unknown_character_error():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("..")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character "."' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("?")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character "?"' in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("\u203B")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character "\\u203B"'
        in excinfo.value.message
    )

    with raises(GraphQLSyntaxError) as excinfo:
        lex_one("\u200b")
    assert (
        'Syntax Error GraphQL (1:1) Unexpected character "\\u200B"'
        in excinfo.value.message
    )


def test_lex_reports_useful_information_for_dashes_in_names():
    # type: () -> None
    q = "a-b"
    lexer = Lexer(Source(q))
    first_token = lexer.next_token()
    assert first_token == Token(TokenKind.NAME, 0, 1, "a")
    with raises(GraphQLSyntaxError) as excinfo:
        lexer.next_token()

    assert (
        'Syntax Error GraphQL (1:3) Invalid number, expected digit but got: "b".'
        in excinfo.value.message
    )
