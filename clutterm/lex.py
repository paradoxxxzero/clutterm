from .colors import color, bold_color, color256
import logging
import re
log = logging.getLogger('clutterm')


class Style(object):
    def __init__(self, fg=None, bg=None, bold=None, reverse=None):
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.reverse = reverse

    def copy(self):
        return Style(self.fg, self.bg, self.bold, self.reverse)

    def __repr__(self):
        if self:
            return "Style(bg=%s, fg=%s, bold=%s, reverse=%s)" % (
                self.bg, self.fg, self.bold, self.reverse)
        else:
            return "Style()"

    def __eq__(self, other):
        return (self.fg == other.fg and
                self.bg == other.bg and
                self.bold == other.bold and
                self.reverse == other.reverse)

    def __bool__(self):
        return (self.fg is not None or
                self.bg is not None or
                self.bold is not None or
                self.reverse is not None)
    __nonzero__ = __bool__


class Char(object):
    def __init__(self, char, style=None):
        self.char = char
        self.style = style or Style()

    def __repr__(self):
        return "Char(%r)[%r]" % (self.char, self.style)


class Cursor(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Matrix(object):
    def __init__(self, cols, rows, void=' '):
        self.cols = cols
        self.rows = rows
        self.void = Char(void)
        self.scroll = 0

        self.matrix = [
            self.create_line() for i in range(self.rows)
        ]

    def putc(self, cursor, char):
        return self.put(cursor.x, cursor.y, char)

    def put(self, x, y, char):
        if (0 <= y < self.rows and
            0 <= x < self.cols):
            self.matrix[y + self.scroll][x] = char
        else:
            log.info('Put %s Out %d %d' % (char, x, y))

    def getc(self, cursor):
        return self.get(cursor.x, cursor.y)

    def get(self, x, y):
        if (0 <= y < self.rows and
            0 <= x < self.cols):
            return self.matrix[y + self.scroll][x]
        else:
            log.info('Get Out %d %d' % (x, y))
            return self.void

    def get_line(self, y):
        if 0 <= y < self.rows:
            return self.matrix[y + self.scroll]

    def shift(self):
        # self.matrix.pop(0)
        self.scroll += 1
        self.matrix.append(self.create_line())

    def clear_line(self, y):
        self.matrix[y + self.scroll] = self.create_line()

    def create_line(self, size=None):
        size = size or self.cols
        return [self.void] * size

    def erase_range(self, rng, y):
        for i in rng:
            self.matrix[y + self.scroll][i] = self.void

    def resize(self, cols, rows):
        if rows > self.rows:
            for i in range(rows - self.rows):
                self.matrix.append(self.create_line())
        # elif rows < self.rows:
            # for i in range(self.rows - rows):
                # self.matrix.pop(0)
        self.rows = rows

        if cols > self.cols:
            for i in range(self.rows):
                self.matrix[i] = self.matrix[i] + self.create_line(
                    cols - self.cols)
        elif cols < self.cols:
            for i in range(self.rows):
                self.matrix[i] = self.matrix[i][:(cols - self.cols)]
        self.cols = cols


escape_chars = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;'
}

csi_re = re.compile(r'\x1b\[(\?)?(\d*)(;(\d*))?(;(\d*))?([a-zA-Z@])')
osc_re = re.compile(r'\x1b\](\d+);(.*)\x07')
dg_re = re.compile(r'\x1b[\(\)\*\+][\w\d=]')
other_re = re.compile(r'\x1b[78=>Fclmno|\}~]')


class Lexer(object):
    """Mayhem parser"""

    def __init__(self, cols, rows, set_title, bell):
        self.cursor = Cursor(0, 0)
        self.alternate_cursor = Cursor(0, 0)
        self.matrix = Matrix(cols, rows)
        self.alternate_matrix = Matrix(cols, rows)
        self.saved_cursor = Cursor(0, 0)
        self.style = Style()
        self.end_style = None
        self.set_title = set_title
        self.bell = bell
        self.text_position = 0
        self.damaged = set()
        self.remaining = ''

    def resize(self, cols, rows):
        self.matrix.resize(cols, rows)
        self.alternate_matrix.resize(cols, rows)
        if self.cursor.x > cols:
            self.cursor.x = cols - 1
        if self.cursor.y > rows:
            self.cursor.y = rows - 1
        log.debug("Damaging on resize")
        self.damaged = set(range(self.rows))

    def lex(self, text):
        self.text_position = 0
        text = self.remaining + text
        while self.text_position != len(text):
            char = text[self.text_position]
            queue = text[self.text_position:]
            csi = csi_re.match(queue)
            osc = osc_re.match(queue)
            dg = dg_re.match(queue)
            other = other_re.match(queue)

            self.text_position += 1

            # Pango escaping
            if char in escape_chars:
                char = escape_chars[char]

            elif csi:
                self.csi(csi)
                self.matrix.getc(self.cursor).style = self.style
                continue

            elif osc:
                self.osc(osc)
                continue

            elif dg:
                # Ignoring Designate G[0-3]
                log.debug('Ignoring designate group %s' % dg.group(0))
                self.text_position += len(dg.group(0)) - 1
                continue

            elif other:
                log.debug('Ignoring escape %s' % other.group(0))
                self.text_position += len(other.group(0)) - 1
                continue

            elif char == '\x1b':
                log.error('Unmatched escape %r' % (
                    text[self.text_position:][:10]))
                log.debug('Trying later')
                self.remaining = queue
                break

            elif char == '\r':
                self.cursor.x = 0
                continue

            elif char == '\n':
                self.cursor.x = 0
                if self.cursor.y == self.rows - 1:
                    self.matrix.shift()
                    log.debug(
                        "Damaging screen because of newline at last line")
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

            if self.cursor.x >= self.cols:
                self.cursor.x = 0
                if self.cursor.y == self.rows - 1:
                    self.matrix.shift()
                    log.debug(
                        "Damaging screen because of newline at last line")
                    self.damaged = set(range(self.rows))
                else:
                    self.cursor.y += 1

            log.debug("Damaging current line %d" % self.cursor.y)
            self.damaged.add(self.cursor.y)
            self.matrix.putc(self.cursor, Char(char, self.style.copy()))
            self.style = self.style.copy()
            self.cursor.x += 1

        self.remaining = ''

    def osc(self, osc):
        m = int(osc.group(1) or -1)
        txt = osc.group(2)
        if m in range(3):
            self.set_title(txt)
        else:
            log.warn('Untreated osc %r' % osc.group(0))
        self.text_position += len(osc.group(0)) - 1

    def csi(self, csi):
        type = csi.group(7)
        opt = csi.group(1) == '?'
        m = int(csi.group(2) or -1)
        n = int(csi.group(4) or -1)
        o = int(csi.group(6) or -1)
        log.debug('csi %r %s %d %d %d' % (opt, type, m, n, o))
        if hasattr(self, 'csi_%s' % type):
            getattr(self, 'csi_%s' % type)(m, n, o, opt)
        else:
            log.warn('Untreated csi of type: %s %r' % (
                type, csi.group(0)))
        self.text_position += len(csi.group(0)) - 1

    def csi_A(self, m, n, o, opt):
        if m == -1:
            m = 1
        if self.cursor.y > 0:
            self.cursor.y -= m

    def csi_B(self, m, n, o, opt):
        if m == -1:
            m = 1
        if self.cursor.y < self.rows:
            self.cursor.y += m

    def csi_C(self, m, n, o, opt):
        if m == -1:
            m = 1
        if self.cursor.x < self.cols:
            self.cursor.x += m

    def csi_D(self, m, n, o, opt):
        if m == -1:
            m = 1
        if self.cursor.x > 0:
            self.cursor.x -= m

    def csi_E(self, m, n, o, opt):
        if m == -1:
            m = 1
        self.cursor.x = 0
        if self.cursor.y < self.rows:
            self.cursor.y += m

    def csi_F(self, m, n, o, opt):
        if m == -1:
            m = 1
        self.cursor.x = 0
        if self.cursor.y > 0:
            self.cursor.y -= m

    def csi_G(self, m, n, o, opt):
        m -= 1
        if 0 <= m <= self.cols:
            self.cursor.x = m

    def csi_H(self, m, n, o, opt):
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

    def csi_J(self, m, n, o, opt):
        if m == 1:
            r = range(0, self.cursor.y)
        elif m == 2:
            r = range(0, self.rows)
        else:
            r = range(self.cursor.y, self.rows)

        for i in r:
            self.matrix.clear_line(i)
            log.debug("Damaging line %i because of csi J" % i)
            self.damaged.add(i)

    def csi_K(self, m, n, o, opt):
        if m == 1:
            r = range(0, self.cursor.x)
        elif m == 2:
            r = range(0, self.cols)
        else:
            r = range(self.cursor.x, self.cols)

        self.matrix.erase_range(r, self.cursor.y)
        log.debug("Damaging line %i because of csi K" % self.cursor.y)
        self.damaged.add(self.cursor.y)

    def csi_X(self, m, n, o, opt):
        if m == -1:
            m = 1

        self.matrix.erase_range(
            range(self.cursor.x, self.cursor.x + m),
            self.cursor.y)
        log.debug("Damaging line %i because of csi X" % self.cursor.y)
        self.damaged.add(self.cursor.y)

    def csi_d(self, m, n, o, opt):
        m -= 1
        if 0 <= m <= self.rows:
            self.cursor.y = m

    def csi_f(self, m, n, o, opt):
        self.csi_H(m, n)

    def csi_h(self, m, n, o, opt):
        if opt and m == 1049:
            self.matrix, self.alternate_matrix = (
                self.alternate_matrix, self.matrix)
            self.cursor, self.alternate_cursor = (
                self.alternate_cursor, self.cursor)
            log.debug("Damaging screen because of csi h")
            self.damaged = set(range(self.rows))

    def csi_l(self, m, n, o, opt):
        if opt and m == 1049:
            self.matrix, self.alternate_matrix = (
                self.alternate_matrix, self.matrix)
            self.cursor, self.alternate_cursor = (
                self.alternate_cursor, self.cursor)
            log.debug("Damaging screen because of csi l")
            self.damaged = set(range(self.rows))

    def csi_m(self, m, n, o, opt):
        if m == -1:
            m = 0

        if n == -1:
            n = m
            m = -1

        if m == 1:
            self.style.bold = True
        if m == 0:
            self.style.bold = False
            self.style.reverse = False

        if n == 0:
            self.style.bold = False
            self.style.reverse = False
            self.style.fg = False
            self.style.bg = False
        elif n == 7:
            self.style.reverse = True
        elif 30 <= n <= 37:
            if m != 1:
                self.style.fg = color[n - 30]
            else:
                self.style.fg = bold_color[n - 30]
        elif n == 39:
            self.style.fg = False
        elif m == 38 and n == 5:
            self.style.fg = color256[o]
        elif 40 <= n <= 47:
            if m != 1:
                self.style.bg = color[n - 40]
            else:
                self.style.bg = bold_color[n - 40]
        elif n == 49:
            self.style.bg = False
        elif m == 48 and n == 5:
            self.style.bg = color256[o]

    def csi_s(self, m, n, o, opt):
        self.saved_cursor = self.cursor

    def csi_u(self, m, n, o, opt):
        self.cursor = self.saved_cursor

    def get_line(self, y):
        line = self.matrix.get_line(y)
        if not line:
            return ''
        line = line[:]

        def make_close_tag(bold):
            tag = ''
            if bold:
                tag += '</b>'
            tag += '</span>'
            return tag

        def make_tag(style):
            log.debug('Make tag with %r' % style)
            fg = style.fg or 'white'
            bg = style.bg

            if style.reverse:
                fg, bg = bg or 'black', fg

            tag = '<span'
            if fg:
                tag += ' foreground="%s"' % fg
            if bg:
                tag += ' background="%s"' % bg
            tag += '>'
            if style.bold:
                tag += '<b>'
            return tag

        if self.end_style:
            current = self.end_style.copy()
        else:
            current = Style()

        current = line[0].style.copy() or Style()  # current
        line[0] = make_tag(current) + line[0].char
        for i in range(1, self.cols):
            style = line[i].style
            if style and style != current:
                log.debug("New style %r with current %r" % (style, current))
                closure = make_close_tag(current.bold)
                if style.fg is not None:
                    current.fg = style.fg

                if style.bg is not None:
                    current.bg = style.bg

                if style.bold is not None:
                    current.bold = style.bold

                if style.reverse is not None:
                    current.reverse = style.reverse

                line[i] = "%s%s%s" % (
                    closure, make_tag(current), line[i].char)
            else:
                line[i] = line[i].char

        line[self.cols - 1] += make_close_tag(current.bold)
        self.end_style = current
        return ''.join(line)

    @property
    def current_fg(self):
        return self.style.fg or 'white'

    @property
    def cols(self):
        return self.matrix.cols

    @property
    def rows(self):
        return self.matrix.rows
