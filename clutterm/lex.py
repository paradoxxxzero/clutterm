import logging
import re
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
    csi_re = re.compile(r'\x1b\[(\?)?(\d*)(;(\d*))?([a-zA-z@])')
    osc_re = re.compile(r'\x1b\](\d+);(.*)\x07')

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
            elif m != 1:
                style = ('</span><span foreground="%s">' %
                        bold_color[n])
            else:
                style = ('</span><span foreground="%s">' %
                        color[n])
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
            csi = self.csi_re.match(self.text[self.position:])
            osc = self.osc_re.match(self.text[self.position:])

            self.position += 1
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
                import pdb
                pdb.set_trace()
                log.error('Unmatched escape %d %r' % (
                    self.position, self.text))
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
