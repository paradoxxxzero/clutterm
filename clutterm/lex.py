import logging
import re
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

csi_re = re.compile(r'\x1b\[(\?)?(\d*)(;(\d*))?([a-zA-z@])')
osc_re = re.compile(r'\x1b\](\d+);(.*)\x07')


class Lexer(object):
    """Mayhem parser"""

    def __init__(self, text, cursor, string, set_title):
        self.text = text
        self.cursor = cursor
        self.string = string
        self.set_title = set_title
        self.position = 0

    def csi(self, csi):
        type = csi.group(5)
        m = int(csi.group(2) or -1)
        n = int(csi.group(4) or -1)
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
            if self.cursor > 0 and self.cursor <= len(self.string):
                self.string[self.cursor - 1] += style
            else:
                log.warn('cursor problem for style %s %d' %
                         (style, self.cursor))
        elif type == 'C':
            self.cursor += n
            if self.cursor > len(self.string):
                log.warn('Self.Cursor too far at %d' % self.cursor)
                self.cursor = len(self.string) - 1
        elif type == 'D':
            self.cursor -= n
            if self.cursor < 0:
                log.warn('Self.Cursor too far at %d' % self.cursor)
                self.cursor = 0
        else:
            log.warn('Untreated csi %r' % csi.group(0))
        self.position += len(csi.group(0)) - 1

    def osc(self, osc):
        m = int(osc.group(1) or -1)
        txt = osc.group(2)
        if m in range(3):
            self.set_title(txt)
        else:
            log.warn('Untreated osc %r' % osc.group(0))
        self.position += len(osc.group(0)) - 1

    def lex(self):

        while self.position != len(self.text):
            char = self.text[self.position]
            csi = csi_re.match(self.text[self.position:])
            osc = osc_re.match(self.text[self.position:])

            self.position += 1

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
                    self.text[self.position:][:10]))
                continue

            elif char == '\r':
                self.cursor = 0
                continue

            elif char == '\n':
                self.cursor = 0
                return self.string, self.text[self.position:], self.cursor

            elif char == '\x08':
                self.cursor -= 1
                continue

            if self.cursor > len(self.string) - 1:
                self.string.append(char)
            else:
                self.string[self.cursor] = char

            self.cursor += 1

        return self.string, None, self.cursor
