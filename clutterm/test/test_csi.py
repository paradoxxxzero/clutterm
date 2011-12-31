from clutterm.lex import Lexer
from clutterm.colors import color


class TestColors(object):
    def test_foreground(self):
        lexer = Lexer(80, 1)
        lexer.lex('Lorem [31mIpsum')
        assert lexer.get_line(0) == (
            '<span foreground="white">Lorem </span>'
            '<span foreground="%s">Ipsum'
            '%s'
            '</span>') % (color[1], ' ' * 69)

    def test_foreground_multi(self):
        lexer = Lexer(80, 1)
        lexer.lex('A[31mB[mC[32mD[0m')
        assert lexer.get_line(0) == (
            '<span foreground="white">A</span>'
            '<span foreground="%s">B</span>'
            '<span foreground="white">C</span>'
            '<span foreground="%s">D</span>'
            '<span foreground="white">'
            '%s'
            '</span>') % (color[1], color[2], ' ' * 76)

    def test_background(self):
        lexer = Lexer(80, 1)
        lexer.lex('A[31m[45mB[mC[42mD[0m')
        assert lexer.get_line(0) == (
            '<span foreground="white">A</span>'
            '<span foreground="%s" background="%s">B</span>'
            '<span foreground="white">C</span>'
            '<span foreground="white" background="%s">D</span>'
            '<span foreground="white">'
            '%s'
            '</span>') % (color[1], color[5], color[2], ' ' * 76)

    def test_reverse(self):
        lexer = Lexer(80, 1)
        lexer.lex('A[31m[45mB[7mC[7mD[0m')
        assert lexer.get_line(0) == (
            '<span foreground="white">A</span>'
            '<span foreground="%s" background="%s">B</span>'
            '<span foreground="%s" background="%s">CD</span>'
            '<span foreground="white">'
            '%s'
            '</span>') % (
                color[1], color[5],
                color[5], color[1],
                ' ' * 76)

    def test_optimize(self):
        lexer = Lexer(80, 1)
        lexer.lex('A[31mB[31mC')
        assert lexer.get_line(0) == (
            '<span foreground="white">A</span>'
            '<span foreground="%s">BC'
            '%s'
            '</span>') % (color[1], ' ' * 77)
