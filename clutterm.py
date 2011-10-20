#!/usr/bin/env python
from gi.repository import Clutter, ClutterX11, GObject
from clutterm.ui import Clutterm
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
log.setLevel(logging.DEBUG if 'debug' in sys.argv
             else logging.INFO if 'info' in sys.argv
             else logging.WARN)

ClutterX11.set_use_argb_visual(True)
GObject.threads_init()
Clutter.threads_init()
Clutter.init(sys.argv)

app = Clutterm()

Clutter.main()
