#!/usr/bin/env python
from gi.repository import Clutter, ClutterX11, GObject
from clutterm.ui import Clutterm
from argparse import ArgumentParser
import logging
import sys
log = logging.getLogger('clutterm')
handler = None
try:
    from log_colorizer import make_colored_stream_handler
    handler = make_colored_stream_handler()
except ImportError:
    handler = logging.StreamHandler()

log.addHandler(handler)

parser = ArgumentParser(
        description='A pure python terminal using clutter',
        prog='clutterm',
        version="0.5")

parser.add_argument(
    '-l', '--log-level',
    default='WARN',
    dest='log_level',
    choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
    help='Set debugging log level')
parser.add_argument(
    "-t", "--transparency",
    type=int,
    default=200,
    dest="transparency",
    help='Background transparency 0 -> no tranparency, 255 -> tranparent'
)
parser.add_argument(
    "-f", "--font-name",
    default='Mono',
    dest="font_name",
    help='Font name'
)
parser.add_argument(
    "-s", "--font-size",
    type=int,
    default=10,
    dest="font_size",
    help='Font size'
)
parser.add_argument(
    "-x", "--execute",
    default=None,
    dest="shell",
    help='Shell command to execute instead of $SHELL'
)

options = parser.parse_args()
log_level = getattr(logging, options.log_level)
log.setLevel(log_level)

options.transparency = max(min(options.transparency, 255), 0)

if options.transparency > 0:
    ClutterX11.set_use_argb_visual(True)

GObject.threads_init()
Clutter.threads_init()
Clutter.init(sys.argv)
Clutter.threads_enter()
clutterm = Clutterm(options)

log.info('Starting main')
Clutter.main()
Clutter.threads_leave()
log.info('Main exited')
clutterm.shell.quit()
