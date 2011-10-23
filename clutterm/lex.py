import logging
import re


class Style(object):
    def __init__(self,
                 fg=None, bg=None, bold=None,
                 reverse=False):
        self.fg = fg
        self.bg = bg
        self.reverse = reverse
        self.bold = bold


class Cursor(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Matrix(object):
    def __init__(self, cols, rows, void=' '):
        self.cols = cols
        self.rows = rows
        self.void = void

        self.matrix = [
            self.create_line() for i in range(self.rows)
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
            return self.void

    def get_line(self, y):
        if 0 <= y < self.rows:
            return self.matrix[y]

    def shift(self):
        self.matrix.pop(0)
        self.matrix.append(self.create_line())

    def clear_line(self, y):
        self.matrix[y] = self.create_line()

    def create_line(self, size=None):
        size = size or self.cols
        return [self.void for i in range(size)]

    def erase_range(self, rng, y):
        for i in rng:
            self.matrix[y][i] = self.void

    def resize(self, cols, rows):
        if rows > self.rows:
            for i in range(rows - self.rows):
                self.matrix.append(self.create_line())
        elif rows < self.rows:
            for i in range(self.rows - rows):
                self.matrix.pop(0)

        if cols > self.cols:
            for i in range(self.rows):
                self.matrix[i] = self.matrix[i] + self.create_line(
                    cols - self.cols)
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
        self.styles = Matrix(cols, rows, None)
        self.styles.put(0, 0, Style('white', 'black'))
        self.end_styles = {}
        self.set_title = set_title
        self.bell = bell
        self.text_position = 0
        self.damaged = set()

    def resize(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.matrix.resize(cols, rows)
        self.styles.resize(cols, rows)
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
                    self.styles.shift()
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
        style = self.styles.get(self.cursor.x, self.cursor.y)
        if not style:
            style = Style()
            self.styles.put(self.cursor.x, self.cursor.y, style)
        style.reverse = None
        if m == -1:
            m = 0

        if n == -1:
            n = m
            m = -1

        if m == 1:
            style.bold = True
        if m == 0:
            style.bold = False

        if n == 0:
            style.fg = 'white'
            style.bg = 'black'
        elif n == 7:
            style.reverse = True
        elif 30 <= n <= 37:
            if m != 1:
                style.fg = color[n - 30]
            else:
                style.fg = bold_color[n - 30]
        elif n == 39:
            style.fg = 'white'
        elif 40 <= n <= 47:
            if m != 1:
                style.bg = color[n - 40]
            else:
                style.bg = bold_color[n - 40]
        elif n == 49:
            style.bg = 'black'

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
            self.matrix.clear_line(i)
            self.styles.clear_line(i)
            self.damaged.add(i)

    def csi_K(self, m, n):
        if m == 1:
            r = range(0, self.cursor.x)
        elif m == 2:
            r = range(0, self.cols - 1)
        else:
            r = range(self.cursor.x, self.cols - 1)

        self.matrix.erase_range(r, self.cursor.y)
        self.styles.erase_range(r, self.cursor.y)

    def csi_d(self, m, n):
        m -= 1
        if 0 <= m <= self.rows:
            self.cursor.y = m

    def csi_f(self, m, n):
        self.csi_H(m, n)

    def get_line(self, y):
        line = self.matrix.get_line(y)
        if not line:
            return ''

        def make_close_tag(bold):
            tag = ''
            if bold:
                tag += '</b>'
            tag += '</span>'
            return tag

        def make_tag(fg, bg, reverse=False, bold=False):
            if reverse:
                fg, bg = bg, fg
            tag = '<span foreground="%s"' % fg
            # Externalize this
            if bg != 'black':
                tag += ' background="%s"' % bg
            tag += '>'
            if bold:
                tag += '<b>'
            return tag

        line = list(line)
        # Externalize this
        fg = 'white'
        bg = 'black'
        bold = False
        reverse = False
        end_style = self.end_styles.get(y - 1, None)
        if end_style:
            fg = end_style.fg
            bg = end_style.bg
            bold = end_style.bold
            reverse = end_style.reverse

        for i in range(0, self.cols):
            style = self.styles.get(i, y)
            if style:
                closure = make_close_tag(bold)
                if style.fg:
                    fg = style.fg
                if style.bg:
                    bg = style.bg
                if style.bold is False:
                    bold = False
                if style.bold:
                    bold = True
                reverse = style.reverse
                line[i] = closure + make_tag(fg, bg, reverse, bold) + line[i]

        line[0] = make_tag(
            fg, bg, end_style and end_style.reverse,
            end_style and end_style.bold) + line[0]
        line[self.cols - 1] += make_close_tag(bold)
        self.end_styles[y] = Style(fg, bg, bold, reverse)
        return ''.join(line)

    @property
    def current_fg(self):
        style = self.styles.getc(self.cursor)
        if style:
            return style.fg or "#ffffff"
        return "#ffffff"
