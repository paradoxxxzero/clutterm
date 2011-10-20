from collections import namedtuple
import logging
import re


class Cursor(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Matrix(object):
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows

        self.matrix = [
            [' ' for i in range(self.cols)]
            for i in range(self.rows)
        ]

    def putc(self, cursor, char):
        return self.put(cursor.x, cursor.y, char)

    def put(self, x, y, char):
        if (0 <= y < self.rows and
            0 <= x < self.cols):
            self.matrix[y][x] = char
        else:
            log.info('Put Out %d %d' % (x, y))

    def getc(self, cursor):
        return self.get(cursor.x, cursor.y)

    def get(self, x, y):
        if (0 <= y < self.rows and
            0 <= x < self.cols):
            return self.matrix[y][x]
        else:
            log.info('Get Out %d %d' % (x, y))
            return ' '

    def get_line(self, y):
        if 0 <= y < self.rows:
            return ''.join(self.matrix[y])
        return ''

log = logging.getLogger('clutterm')
color = {
    30: '#262524',
    31: '#bf4646',
    32: '#67b25f',
    33: '#cfc44e',
    34: '#516083',
    35: '#ca6eff',
    36: '#92b2f8',
    37: '#d5d5d5',
    40: '#292827',
    41: '#f48a8a',
    42: '#a5d79f',
    43: '#e1da84',
    44: '#a2bbff',
    45: '#e2b0ff',
    46: '#bacdf8',
    47: '#ffffff'
}

bold_color = {
    30: '#292827',
    31: '#f48a8a',
    32: '#a5d79f',
    33: '#e1da84',
    34: '#a2bbff',
    35: '#e2b0ff',
    36: '#bacdf8',
    37: '#ffffff'
}


class Lexer(object):
    """Mayhem parser"""

    escape_chars = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;'
    }
    csi_re = re.compile(r'\x1b\[(\?)?(\d*)(;(\d*))?([a-zA-Z@])')
    osc_re = re.compile(r'\x1b\](\d+);(.*)\x07')

    def __init__(self, cols, rows, set_title, bell):
        self.cursor = Cursor(0, 0)
        self.cols = cols
        self.rows = rows
        self.matrix = Matrix(cols, rows)
        self.set_title = set_title
        self.bell = bell
        self.text_position = 0
        self.damaged_lines = set()

    def csi(self, csi):
        type = csi.group(5)
        opt = csi.group(1)
        m = int(csi.group(2) or -1)
        n = int(csi.group(4) or -1)
        log.debug('csi %r %s %d %d' % (opt, type, m, n))
        if type == 'm':
            if n < 30 or n in (39, 49):
                style = '</span><span>'
            elif m != 1:
                style = ('</span><span foreground="%s">' %
                        bold_color[n])
            else:
                style = ('</span><span foreground="%s">' %
                        color[n])
            # FIXME!!!!
            self.matrix.put(
                self.cursor.y, self.cursor.x - 1,
                self.matrix.get(
                    self.cursor.y, self.cursor.x - 1)
                + style)

        elif type == 'C':
            self.cursor.x += m
            if self.cursor.x > self.cols:
                log.warn('Self.Cursor.X too far at %d' % self.cursor.x)
                self.cursor.x = self.cols - 1
        elif type == 'D':
            self.cursor.x -= m
            if self.cursor.x < 0:
                log.warn('Self.Cursor.X too far at %d' % self.cursor.x)
                self.cursor.x = 0
        elif type == 'K':
            if m == 1:
                r = range(0, self.cursor.x)
            elif m == 2:
                r = range(0, self.cols - 1)
            else:
                r = range(self.cursor.x, self.cols - 1)
                for i in r:
                    self.matrix.put(self.cursor.y, i, ' ')
        else:
            log.warn('Untreated csi %r' % csi.group(0))
        self.text_position += len(csi.group(0)) - 1

    def osc(self, osc):
        m = int(osc.group(1) or -1)
        txt = osc.group(2)
        if m in range(3):
            self.set_title(txt)
        else:
            log.warn('Untreated osc %r' % osc.group(0))
        self.text_position += len(osc.group(0)) - 1

    def lex(self, text):
        self.text_position = 0
        while self.text_position != len(text):
            char = text[self.text_position]
            csi = self.csi_re.match(text[self.text_position:])
            osc = self.osc_re.match(text[self.text_position:])

            self.text_position += 1
            # Pango escaping
            if char in self.escape_chars:
                char = self.escape_chars[char]

            elif csi:
                self.csi(csi)
                continue

            elif osc:
                self.osc(osc)
                continue
            elif char == '\x1b':
                log.error('Unmatched escape %d %r' % (
                    self.text_position, text))
                continue

            elif char == '\r':
                self.cursor.x = 0
                continue

            elif char == '\n':
                self.cursor.x = 0
                self.cursor.y += 1

            elif char == '\x08':
                self.cursor.x -= 1
                continue
            elif char == '\x07':
                self.bell()
                continue

            self.damaged_lines.add(self.cursor.y)
            self.matrix.putc(self.cursor, char)
            self.cursor.x += 1
