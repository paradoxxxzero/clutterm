from gi.repository import Clutter
from .shell import Shell
import logging
log = logging.getLogger('clutterm')


# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255, 255, 255, 255)
colorRed = Clutter.Color.new(255, 0, 0, 255)
colorBlack = Clutter.Color.new(0, 0, 0, 0)


class Clutterm(object):

    def __init__(self):
        """
        Build the user interface.
        """
        self.mainStage = Clutter.Stage.get_default()
        self.mainStage.set_color(colorBlack)
        self.mainStage.set_title("Clutterminal")
        self.mainStage.set_size(800, 600)
        self.mainStage.set_reactive(True)

        # Create lines layout
        self.linesBoxManager = Clutter.BoxLayout()
        self.linesBoxManager.set_vertical(True)
        self.linesBoxManager.set_homogeneous(False)
        self.linesBoxManager.set_pack_start(False)
        self.linesBoxManager.set_use_animations(True)
        self.linesBoxManager.set_easing_duration(100)

        # Create line layout
        self.lineManager = Clutter.BoxLayout()
        self.lineManager.set_homogeneous(False)
        self.lineManager.set_pack_start(False)
        self.lineManager.set_use_animations(True)
        self.lineManager.set_easing_duration(100)

        # Create the lines box
        self.linesBox = Clutter.Box.new(self.linesBoxManager)
        self.linesBox.set_color(colorBlack)
        self.mainStage.add_actor(self.linesBox)
        self.line = None

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
        self.reader = Clutter.Timeline.new(1)
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
                    self.new_line()
                    self.cursor = 0
                else:
                    self._write(char)
                    self.cursor += 1

    def _write(self, text, color=colorWhite):
        if self.cursor < len(Clutter.Container.get_children(self.line)):
            Clutter.Container.get_children(
                self.line)[self.cursor].set_text(text)
        else:
            ctext = Clutter.Text.new_full("Mono 10", text, color)
            Clutter.Container.add_actor(self.line, ctext)
            ctext.show()

    def new_line(self):
        self.line = Clutter.Box.new(self.lineManager)
        self.line.set_color(colorBlack)
        self.linesBoxManager.set_alignment(self.line, 0, 0)
        self.linesBox.add_actor(self.line)
        # self.line.add_effect(Clutter.BlurEffect())

    def destroy(self):
        Clutter.main_quit()

    def onKeyPress(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        val = event.key.unicode_value
        if val == 65288:
            children = Clutter.Container.get_children(self.line)
            if len(children) > 0:
                Clutter.Container.remove_actor(
                    self.line,
                    children[-1])

        self.shell.write(val)
        if val == '\x04':
            self.destroy()

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

        # if (modControl and char == 'd'):
