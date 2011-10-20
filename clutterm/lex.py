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
            log.info('Put %s Out %d %d' % (char, x, y))

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

    def shift(self):
        self.matrix.pop(0)
        self.matrix.append([' ' for i in range(self.cols)])


log = logging.getLogger('clutterm')
color = (
    '#262524',
    '#bf4646',
    '#67b25f',
    '#cfc44e',
    '#516083',
    '#ca6eff',
    '#92b2f8',
    '#d5d5d5'
)

bold_color = (
    '#292827',
    '#f48a8a',
    '#a5d79f',
    '#e1da84',
    '#a2bbff',
    '#e2b0ff',
    '#bacdf8',
    '#ffffff'
)

escape_chars = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;'
}

csi_re = re.compile(r'\x1b\[(\?)?(\d*)(;(\d*))?([a-zA-Z@])')
osc_re = re.compile(r'\x1b\](\d+);(.*)\x07')


class Lexer(object):
    """Mayhem parser"""

    def __init__(self, cols, rows, set_title, bell):
        self.cursor = Cursor(0, 0)
        self.cols = cols
        self.rows = rows
        self.matrix = Matrix(cols, rows)
        self.set_title = set_title
        self.bell = bell
        self.text_position = 0
        self.damaged = set()

    def csi(self, csi):
        type = csi.group(5)
        opt = csi.group(1)
        m = int(csi.group(2) or -1)
        n = int(csi.group(4) or -1)
        log.debug('csi %r %s %d %d' % (opt, type, m, n))
        if type == 'm':
            if n < 30 or n in (39, 49):
                style = '</span><span>'

            elif 30 <= n <= 37:
                if m != 1:
                    style = ('</span><span foreground="%s">' %
                             color[n - 30])
                else:
                    style = ('</span><span foreground="%s">' %
                             bold_color[n - 30])
            elif 40 <= n <= 47:
                if m != 1:
                    style = ('</span><span background="%s">' %
                             color[n - 40])
                else:
                    style = ('</span><span background="%s">' %
                             bold_color[n - 40])
            # FIXME
            self.matrix.put(
                self.cursor.x - 1, self.cursor.y,
                self.matrix.get(
                    self.cursor.x - 1, self.cursor.y)
                + style)

        elif type == 'C':
            self.cursor.x += m
            if self.cursor.x > self.cols:
                log.warn('cursor too far at %d' % self.cursor.x)
                self.cursor.x = self.cols - 1
        elif type == 'D':
            self.cursor.x -= m
            if self.cursor.x < 0:
                log.warn('cursor too far at %d' % self.cursor.x)
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
            csi = csi_re.match(text[self.text_position:])
            osc = osc_re.match(text[self.text_position:])

            self.text_position += 1

            # Pango escaping
            if char in escape_chars:
                char = escape_chars[char]

            elif csi:
                self.csi(csi)
                continue

            elif osc:
                self.osc(osc)
                continue
            elif char == '\x1b':
                log.error('Unmatched escape %r' % (
                    text[self.text_position:][:10]))
                continue

            elif char == '\r':
                self.cursor.x = 0
                continue

            elif char == '\n':
                self.cursor.x = 0
                if self.cursor.y == self.rows - 1:
                    self.matrix.shift()
                    self.damaged = set(range(self.rows))
                else:
                    self.cursor.y += 1
                continue

            elif char == '\x08':
                self.cursor.x -= 1
                continue
            elif char == '\x07':
                self.bell()
                continue

            self.damaged.add(self.cursor.y)
            self.matrix.putc(self.cursor, char)
            self.cursor.x += 1
