from attest import Tests, assert_hook
from gi.repository import Clutter
from clutterm.ui import Clutterm
from clutterm.shell import Shell
import os
ui = Tests()


@ui.test
def display():
    Clutter.init([])
    app = Clutterm()
    app.new_line()
    for c in "Text to display on line 1":
        app.write(c)
    app.new_line()
    for c in "Text to display on line 2":
        app.write(c)
    Clutter.main()
