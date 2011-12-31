from clutterm.lex import Lexer


def nop():
    pass


def test_cursor():
    lexer = Lexer(10, 3, nop, nop)
    assert lexer.matrix.cols == 10
    assert lexer.matrix.rows == 3
    assert lexer.matrix.scroll == 0
    assert len(lexer.matrix.matrix[0]) == 10
    assert len(lexer.matrix.matrix) == 3
    assert lexer.cursor.x == 0
    assert lexer.cursor.y == 0
    lexer.lex('test')
    assert lexer.cursor.x == 4
    assert lexer.cursor.y == 0
    lexer.lex(' ')
    assert lexer.cursor.x == 5
    assert lexer.cursor.y == 0
    lexer.lex('test')
    assert lexer.cursor.x == 9
    assert lexer.cursor.y == 0
    lexer.lex('...')
    assert lexer.cursor.x == 2
    assert lexer.cursor.y == 1
    lexer.lex('.' * 18)
    assert lexer.cursor.x == 10
    assert lexer.cursor.y == 2
    assert lexer.matrix.scroll == 0
    lexer.lex('.')
    assert lexer.matrix.scroll == 1
    assert lexer.cursor.x == 1
    assert lexer.cursor.y == 2
