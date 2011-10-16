from gi.repository import Clutter
from .shell import Shell
from .shader import shaders
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
        self.mainStage.set_size(800, 600)
        self.mainStage.set_reactive(True)
        self.mainStage.set_use_alpha(True)
        self.mainStage.set_opacity(0)

        # Create lines layout
        self.linesBoxManager = Clutter.BoxLayout()
        self.linesBoxManager.set_vertical(True)
        self.linesBoxManager.set_homogeneous(False)
        self.linesBoxManager.set_pack_start(False)

        # Globals
        self.string = []
        self.line = None
        self.stay = False

        # Create the lines box
        self.linesBox = Clutter.Box.new(self.linesBoxManager)
        self.linesBox.set_color(colorBlack)
        self.mainStage.add_actor(self.linesBox)

        # Make the main window fill the entire stage
        mainGeometry = self.mainStage.get_geometry()
        self.linesBox.set_geometry(mainGeometry)

        # Present the main stage (and make sure everything is shown)
        self.mainStage.show_all()

    def interact(self):
        self.shell = Shell()
        self.cursor = 0
        self.new_line()

        def update(read):
            self.write(self.shell.read())

        # This is so bad...
        # Really need to find a way to put a thread or an asyncore
        # Without clutter threading problems
        # Polling for now
        self.reader = Clutter.Timeline.new(10)
        self.reader.set_loop(True)
        self.reader.connect('completed', update)
        self.reader.start()

        # Setup some key bindings on the main stage
        self.mainStage.connect_after("key-press-event", self.onKeyPress)

    def write(self, text):
        if text != '':
            for char in text:
                if char == '\r':
                    self.cursor = 0
                elif char == '\n':
                    self.line.set_text(''.join(self.string))
                    self.string = []
                    self.new_line()
                    self.cursor = 0
                else:
                    if self.cursor > len(self.string) - 1:
                        self.string.append(char)
                    else:
                        self.string[self.cursor] = char

                    if not self.stay:
                        self.cursor += 1
                    else:
                        self.stay = False

            self.line.set_text(''.join(self.string))

    def new_line(self):
        children = Clutter.Container.get_children(self.linesBox)
        if len(children) > self.shell.rows:
            children[0].destroy()

        self.line = Clutter.Text.new_full("Mono 10", '', colorWhite)
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

        if uval == '\x08':
            if self.cursor > 0:
                self.cursor -= 1
                # Find a better way
                self.stay = True
        if uval == '\x04':
            self.destroy()

        if uval != '':
            self.shell.write(uval)
        else:
            if kval in shaders:
                shaders[kval](self.linesBox)

        #     # Evaluate the key modifiers
        #     state = event.get_state()
        #     if (state & state.SHIFT_MASK == state.SHIFT_MASK):
        #         modShift = True
        #     else:
        #         modShift = False

        #     if (state & state.CONTROL_MASK == state.CONTROL_MASK):
        #         modControl = True
        #     else:
        #         modControl = False

        #     if (state & state.META_MASK == state.META_MASK):
        #         modMeta = True
        #     else:
        #         modMeta = False

