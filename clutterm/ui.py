from gi.repository import Clutter
from .shell import Shell, ReaderAsync
from .shader import shaders
from .bindings import special_keys
from .lex import Lexer

import logging
log = logging.getLogger('clutterm')

# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255, 255, 255, 255)
colorRed = Clutter.Color.new(255, 0, 0, 255)
colorBlack = Clutter.Color.new(0, 0, 0, 200)


class Clutterm(object):

    def __init__(self):
        """
        Build the user interface.
        """
        self.mainStage = Clutter.Stage.new()
        self.mainStage.set_title("Clutterminal")
        self.mainStage.set_reactive(True)
        self.mainStage.set_user_resizable(True)
        self.mainStage.set_use_alpha(True)
        self.mainStage.set_opacity(0)

        # Create lines layout
        self.linesBoxManager = Clutter.BoxLayout()
        self.linesBoxManager.set_vertical(True)
        self.linesBoxManager.set_homogeneous(False)
        self.linesBoxManager.set_pack_start(False)

        # Globals
        self.line = None
        self.stay = False
        self.cursor = 0

        # Create the lines box
        self.linesBox = Clutter.Box.new(self.linesBoxManager)
        self.linesBox.set_color(colorBlack)
        self.mainStage.add_actor(self.linesBox)

        # Make the main window fill the entire stage
        def resize(w, h):
            # TODO Recompute rows and cols
            mainGeometry = self.mainStage.get_geometry()
            self.linesBox.set_geometry(mainGeometry)

        self.mainStage.connect_after("notify::width", resize)
        self.mainStage.connect_after("notify::height", resize)
        self.mainStage.set_size(800, 600)

        # Present the main stage (and make sure everything is shown)
        self.mainStage.show_all()

    def interact(self):
        self.shell = Shell(end_callback=self.destroy)
        self.radix = [' ' for i in range(self.shell.cols)]
        self.new_line()
        self.thread = ReaderAsync(self.shell, self.write)
        self.thread.start()

        # Setup key bindings on the terminal
        self.mainStage.connect_after("key-press-event", self.onKeyPress)

    def write(self, text):
        if text == '':
            return
        remaining = text

        while remaining:
            string, remaining, self.cursor = Lexer(
                remaining, self.cursor, self.radix,
                self.set_title, self.bell).lex()
            self.set_line(''.join(string))
            if remaining is not None:
                self.radix = [' ' for i in range(self.shell.cols)]
                string = []
                self.new_line()

        self.radix = string

    def set_title(self, text):
        self.mainStage.set_title(text)

    def bell(self):
        center = Clutter.Vertex()
        center.x = self.linesBox.get_width() / 2
        center.y = self.linesBox.get_height() / 2
        center.z = 0
        self.linesBox.animatev(
            Clutter.AnimationMode.EASE_OUT_BACK, 100,
            (
                "fixed::scale-x",
                "fixed::scale-y",
                "fixed::scale-center-x",
                "fixed::scale-center-y",
                "scale-x",
                "scale-y"
            ), (
                1.2,
                1.2,
                self.linesBox.get_width() / 2,
                self.linesBox.get_height() / 2,
                1,
                1
            )
        )

    def set_line(self, text):
        log.debug("D %r" % text)
        self.line.set_markup('<span>%s</span>' % text)

    def new_line(self):
        children = Clutter.Container.get_children(self.linesBox)
        if len(children) > self.shell.rows:
            children[0].destroy()

        self.line = Clutter.Text()
        self.line.set_font_name("Mono 10")
        self.line.set_color(colorWhite)
        # self.line.set_editable(True)
        # self.line.set_selectable(True)
        # self.line.set_cursor_visible(True)
        self.linesBoxManager.set_alignment(self.line, 0, 0)
        self.linesBox.add_actor(self.line)

    def destroy(self):
        Clutter.main_quit()

    def onKeyPress(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        uval = event.key.unicode_value
        kval = event.key.keyval

        log.debug('u %r v %d' % (uval, kval))

        if uval != '':
            self.shell.write(uval)
            return

        if kval in special_keys:
            self.shell.write(special_keys[kval])
            return

        if kval in shaders:
            shaders[kval](self.linesBox)
            return

        log.warn('Unknown keyval %d' % kval)
