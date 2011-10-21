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
            log.debug('Put %s Out %d %d' % (char, x, y))

    def getc(self, cursor):
        return self.get(cursor.x, cursor.y)

    def get(self, x, y):
        if (0 <= y < self.rows and
            0 <= x < self.cols):
            return self.matrix[y][x]
        else:
            log.debug('Get Out %d %d' % (x, y))
            return ' '

    def get_line(self, y):
        if 0 <= y < self.rows:
            return ''.join(self.matrix[y])
        return ''

    def shift(self):
        self.matrix.pop(0)
        self.matrix.append([' ' for i in range(self.cols)])

    def clear(self, y):
        self.matrix[y] = [' ' for i in range(self.cols)]

    def resize(self, cols, rows):
        if rows > self.rows:
            for i in range(rows - self.rows):
                self.matrix.append([' ' for i in range(self.cols)])
        elif rows < self.rows:
            for i in range(self.rows - rows):
                self.matrix.pop(0)

        if cols > self.cols:
            for i in range(self.rows):
                self.matrix[i] = self.matrix[i] + [
                    ' ' for i in range(self.cols)]
        elif cols < self.cols:
            for i in range(self.rows):
                self.matrix[i] = self.matrix[i][:(self.cols - cols)]
        self.cols = cols
        self.rows = rows


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
dg_re = re.compile(r'\x1b[\(\)\*\+][\w\d=]')


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

    def resize(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.matrix.resize(cols, rows)
        if self.cursor.x > cols:
            self.cursor.x = cols - 1
        if self.cursor.y > rows:
            self.cursor.y = rows - 1

    def lex(self, text):
        self.text_position = 0
        while self.text_position != len(text):
            char = text[self.text_position]
            csi = csi_re.match(text[self.text_position:])
            osc = osc_re.match(text[self.text_position:])
            dg = dg_re.match(text[self.text_position:])

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

            elif dg:
                # Ignoring Designate G[0-3]
                self.text_position += len(dg.group(0)) - 1
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

    def osc(self, osc):
        m = int(osc.group(1) or -1)
        txt = osc.group(2)
        if m in range(3):
            self.set_title(txt)
        else:
            log.warn('Untreated osc %r' % osc.group(0))
        self.text_position += len(osc.group(0)) - 1

    def csi(self, csi):
        type = csi.group(5)
        opt = csi.group(1)
        m = int(csi.group(2) or -1)
        n = int(csi.group(4) or -1)
        log.debug('csi %r %s %d %d' % (opt, type, m, n))
        if hasattr(self, 'csi_%s' % type):
            getattr(self, 'csi_%s' % type)(m, n)
        else:
            log.warn('Untreated csi %r' % csi.group(0))
        self.text_position += len(csi.group(0)) - 1

    def csi_m(self, m, n):
        if n == -1:
            n = m
            m = -1
        if n == 7:
            #FIXME
            style = '</span><span foreground="black" background="white">'
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
        else:
            style = '</span><span>'
        # FIXME
        self.matrix.put(
            self.cursor.x - 1, self.cursor.y,
            self.matrix.get(
                self.cursor.x - 1, self.cursor.y)
            + style)

    def csi_A(self, m, n):
        if m == -1:
            m = 1
        if self.cursor.y > 0:
            self.cursor.y -= m

    def csi_B(self, m, n):
        if m == -1:
            m = 1
        if self.cursor.y < self.rows:
            self.cursor.y += m

    def csi_C(self, m, n):
        if m == -1:
            m = 1
        if self.cursor.x < self.cols:
            self.cursor.x += m

    def csi_D(self, m, n):
        if m == -1:
            m = 1
        if self.cursor.x > 0:
            self.cursor.x -= m

    def csi_E(self, m, n):
        if m == -1:
            m = 1
        self.cursor.x = 0
        if self.cursor.y < self.rows:
            self.cursor.y += m

    def csi_F(self, m, n):
        if m == -1:
            m = 1
        self.cursor.x = 0
        if self.cursor.y > 0:
            self.cursor.y -= m

    def csi_G(self, m, n):
        m -= 1
        if 0 <= m <= self.cols:
            self.cursor.x = m

    def csi_H(self, m, n):
        if m == -1:
            m = 1
        if n == -1:
            n = 1
        m -= 1
        n -= 1
        if (0 <= n < self.cols and
            0 <= m < self.rows):
            self.cursor.x = n
            self.cursor.y = m

    def csi_J(self, m, n):
        if m == 1:
            r = range(0, self.cursor.y)
        elif m == 2:
            r = range(0, self.rows)
        else:
            r = range(self.cursor.y, self.rows)

        for i in r:
            self.matrix.clear(i)
            self.damaged.add(i)

    def csi_K(self, m, n):
        if m == 1:
            r = range(0, self.cursor.x)
        elif m == 2:
            r = range(0, self.cols - 1)
        else:
            r = range(self.cursor.x, self.cols - 1)

        for i in r:
            self.matrix.put(i, self.cursor.y, ' ')

    def csi_d(self, m, n):
        m -= 1
        if 0 <= m <= self.rows:
            self.cursor.y = m

    def csi_f(self, m, n):
        self.csi_H(m, n)
