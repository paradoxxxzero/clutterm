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
        self.font = "Mono 10"
        self.mainStage = Clutter.Stage.new()
        self.mainStage.set_title("Clutterminal")
        self.mainStage.set_reactive(True)
        self.mainStage.set_user_resizable(True)
        self.mainStage.set_use_alpha(True)
        self.mainStage.set_color(colorBlack)

        # Create lines layout
        self.linesBoxManager = Clutter.BoxLayout()
        self.linesBoxManager.set_vertical(True)
        self.linesBoxManager.set_homogeneous(False)
        self.linesBoxManager.set_pack_start(False)
        # self.linesBoxManager.set_use_animations(True)
        # self.linesBoxManager.set_easing_duration(250)

        # Create the lines box
        self.linesBox = Clutter.Box.new(self.linesBoxManager)
        self.mainStage.add_actor(self.linesBox)
        dummy_text = Clutter.Text()
        dummy_text.set_font_name(self.font)
        dummy_text.set_text("m")
        self.char_width = dummy_text.get_width()
        self.char_height = dummy_text.get_height()

        self.shell = Shell(end_callback=self.destroy)
        self.lexer = Lexer(self.shell.cols, self.shell.rows,
                           self.set_title, self.bell)

        self.cursor = Clutter.Rectangle()
        self.cursor.set_color(Clutter.Color.new(255, 255, 255, 100))
        self.cursor.set_x(self.char_width * self.lexer.cursor.x)
        self.cursor.set_y(self.char_height * self.lexer.cursor.y)
        self.cursor.set_width(self.char_width)
        self.cursor.set_height(self.char_height)
        self.mainStage.add_actor(self.cursor)

        def resize(a0, a1):
            w = self.mainStage.get_width()
            h = self.mainStage.get_height()
            cols = int(w / self.char_width)
            rows = int(h / self.char_height)
            log.info('resize %s %s %s %s' % (w, h, cols, rows))
            self.shell.resize(cols, rows)
            self.lexer.resize(cols, rows)
            self.linesBox.set_geometry(self.mainStage.get_geometry())
            if rows > len(self.lines):
                for i in range(rows - len(self.lines)):
                    self.lines.append(create_line())

        def create_line():
            line = Clutter.Text()
            line.set_color(colorWhite)
            line.set_cursor_color(colorRed)
            line.set_selected_text_color(colorRed)
            line.set_font_name(self.font)
            # self.line.set_editable(True)
            line.set_selectable(True)
            line.set_cursor_visible(True)
            self.linesBoxManager.set_alignment(line, 0, 0)
            self.linesBox.add_actor(line)
            return line

        self.lines = [create_line()
                      for i in range(self.shell.rows)]

        self.thread = ReaderAsync(self.shell, self.write)
        self.thread.start()

        # Setup key bindings on the terminal
        self.mainStage.connect_after("key-press-event", self.onKeyPress)

        self.mainStage.connect_after("notify::width", resize)
        self.mainStage.connect_after("notify::height", resize)
        self.mainStage.set_size(
            self.shell.cols * self.char_width,
            self.shell.rows * self.char_height)

        # Present the main stage (and make sure everything is shown)
        self.mainStage.show_all()

    def write(self, text):
        if text == '':
            return

        self.lexer.lex(text)
        for line in self.lexer.damaged:
            self.set_line(line, self.lexer.get_line(line))
        self.lexer.damaged = set()
        self.cursor.animatev(
            Clutter.AnimationMode.EASE_OUT_BACK, 100,
            (
                "x",
                "y"
            ), (
                self.char_width * self.lexer.cursor.x,
                self.char_height * self.lexer.cursor.y
            )
        )

    def set_title(self, text):
        self.mainStage.set_title(text)

    def bell(self):
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

    def set_line(self, line, text):
        log.debug("D%d %r" % (line, text))
        self.lines[line].set_markup(text)

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

        if kval == 65299:
            import pdb
            pdb.pm()

        log.warn('Unknown keyval %d' % kval)
