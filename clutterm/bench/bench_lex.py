from clutterm.bench import Timer
from clutterm.lex import Lexer
import os


def bench_simple_text_single_pass():
    for cols, rows in ((10, 10), (50, 25), (50, 100)):
        for size in (10, 100, 1000, 2000, 5000, 10000):
            random = str(os.urandom(size))
            lexer = Lexer(cols, rows)
            lex_timer = Timer()
            get_line_timer = Timer()
            with lex_timer:
                lexer.lex(random)
            with get_line_timer:
                for i in range(rows):
                    lexer.get_line(i)
            print("Term size: \x1b[31m%d, %d\t"
                  "\x1b[mText size: \x1b[32m%d\x1b[m \x1b[65`"
                  "[lex: \x1b[33m%dms\x1b[m\t get_line: \x1b[34m%dms\x1b[m]" %
              (cols, rows, size, lex_timer.time, get_line_timer.time))


if __name__ == "__main__":
    bench_simple_text_single_pass()
