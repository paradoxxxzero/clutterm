from gi.repository import Clutter
from .shell import Shell
import logging
log = logging.getLogger('clutterm')


# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255, 255, 255, 255)
colorRed = Clutter.Color.new(255, 0, 0, 255)
colorBlack = Clutter.Color.new(0, 0, 0, 0)


class Clutterm:
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

        # Make the main window fill the entire stage
        mainGeometry = self.mainStage.get_geometry()
        self.linesBox.set_geometry(mainGeometry)

        # Present the main stage (and make sure everything is shown)
        self.mainStage.show_all()

    def interact(self):
        self.shell = Shell()
        self.new_line()
        self.write(self.shell.read())
        self.write(self.shell.read())

        # Setup some key bindings on the main stage
        self.mainStage.connect_after("key-press-event", self.onKeyPress)

    def write(self, text):
        text = text.replace('\r', '\n')
        lines = text.split('\n')
        for line in lines:
            self._write(line)
            if line is not lines[0]:
                self.new_line()

    def _write(self, text, color=colorWhite):
        if text != '':
            self.clutterText = Clutter.Text.new_full("Mono 10", text, color)
            Clutter.Container.add_actor(self.line, self.clutterText)
            self.clutterText.show()

    def new_line(self):
        self.line = Clutter.Box.new(self.lineManager)
        self.line.set_color(colorBlack)
        self.linesBoxManager.set_alignment(self.line, 0, 0)
        self.linesBox.add_actor(self.line)

    def destroy(self):
        Clutter.main_quit()

    def onKeyPress(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        if event.key.keyval > 255:
            if event.key.keyval == 65293:  # enter
                self.shell.write('\n')
                self.write(self.shell.read())
        else:
            char = chr(event.key.keyval)
            # Evaluate the key modifiers
            state = event.get_state()
            if (state & state.SHIFT_MASK == state.SHIFT_MASK):
                modShift = True
            else:
                modShift = False

            if (state & state.CONTROL_MASK == state.CONTROL_MASK):
                modControl = True
            else:
                modControl = False

            if (state & state.META_MASK == state.META_MASK):
                modMeta = True
            else:
                modMeta = False

            self.shell.write(char)
            self.write(self.shell.read())

            if (modControl and char == 'd'):
                self.destroy()
