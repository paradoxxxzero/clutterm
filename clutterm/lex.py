import logging
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


def lex(text, cursor, string, set_title):
    """Mayhem function"""
    i = 0
    while i != len(text):
        char = text[i]
        i += 1
        # Pango escaping
        if char == '<':
            char = '&lt;'
        elif char == '>':
            char = '&gt;'
        elif char == '&':
            char = '&amp;'
        elif char == '\x1b':
            # Term Escape
            if text[i] == ']':
                i += 3  # Ignoring other controls
                title = ''
                # OSC
                while text[i] != '\x07':
                    title += text[i]
                    i += 1
                set_title(title)
                i += 1
                continue
            elif text[i] == '[':
                # CSI
                i += 1
                if text[i] in ('J', 'K'):
                    i += 1
                    continue
                elif text[i].isdigit():
                    # Looking for \e[m;n
                    m = ''
                    n = ''
                    while text[i].isdigit():
                        n += text[i]
                        i += 1
                    n = int(n)
                    if text[i] == ';':
                        m, n = n, ''
                        i += 1
                        while text[i].isdigit():
                            n += text[i]
                            i += 1
                        n = int(n)
                    else:
                        m = 0
                    type = text[i]
                    log.debug('Got type %s with n %d and m %d' %
                             (type, n, m))
                    if type == 'C':
                        cursor += n
                        if cursor > len(string):
                            log.warn('Cursor too far at %d' % cursor)
                            cursor = len(string) - 1
                    if type == 'D':
                        cursor -= n
                        if cursor < 0:
                            log.warn('Cursor too far at %d' % cursor)
                            cursor = 0
                    if type == 'm':
                        if n < 30 or n in (39, 49):
                            char = '</span><span>'
                        elif m == 1:
                            char = ('</span><span foreground="%s">' %
                                    bold_color[n])
                        else:
                            char = ('</span><span foreground="%s">' %
                                    color[n])
                        # FIXME
                        if cursor > 0:
                            string[cursor - 1] += char
                    i += 1
                    continue
        elif char == '\r':
            cursor = 0
            continue
        elif char == '\n':
            return string, text[i:], cursor
        elif char == '\x08':
            cursor -= 1
            continue
        if cursor > len(string) - 1:
            string.append(char)
        else:
            string[cursor] = char
        cursor += 1
    return string, None, cursor
