from gi.repository import Clutter
import sys
import subprocess

DEBUG = False
debugArgs = ['--clutter-debug=all', '--cogl-debug=all']


# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255, 255, 255, 255)
colorRed = Clutter.Color.new(255, 0, 0, 255)
colorBlack = Clutter.Color.new(0, 0, 0, 0)


class GUI:
    def __init__(self):
        """
        Build the user interface.
        """
        self.mainStage = Clutter.Stage.get_default()
        self.mainStage.set_color(colorBlack)
        self.mainStage.set_title("Clutterminal")
        self.mainStage.set_size(800, 600)
        self.mainStage.set_reactive(True)

        # Create a main layout manager
        self.mainLayoutManager = Clutter.BoxLayout()
        self.mainLayoutManager.set_vertical(True)
        self.mainLayoutManager.set_homogeneous(False)
        self.mainLayoutManager.set_pack_start(False)
        self.mainLayoutManager.set_use_animations(True)
        self.mainLayoutManager.set_easing_duration(100)

        # Create the main window
        self.mainWindow = Clutter.Box.new(self.mainLayoutManager)
        self.mainWindow.set_color(colorBlack)
        self.mainStage.add_actor(self.mainWindow)

        # Make the main window fill the entire stage
        mainGeometry = self.mainStage.get_geometry()
        self.mainWindow.set_geometry(mainGeometry)
        self.text = ''
        self.newLine()

        # Setup some key bindings on the main stage
        self.mainStage.connect_after("key-press-event", self.onKeyPress)

        # Present the main stage (and make sure everything is shown)
        self.mainStage.show_all()

    def writeLine(self, text, color=colorWhite):
        txtFont = "Mono 10"
        self.clutterText = Clutter.Text.new_full(
            txtFont, text, color)
        Clutter.Container.add_actor(self.mainWindow, self.clutterText)
        self.mainLayoutManager.set_alignment(self.clutterText, 0, 0)
        self.clutterText.show()

    def newLine(self):
        """
        Create a ClutterText with the phrase Hello World
        """
        if self.text:
            try:
                process = subprocess.Popen(self.text.split(' ')[1:],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True,
                                           executable='/bin/zsh',
                                           cwd='/home/zero')
                outerr = process.communicate()

                for line in outerr[0].split('\n'):
                    self.writeLine(line)
                for line in outerr[1].split('\n'):
                    self.writeLine(line, colorRed)
            except Exception as e:
                self.writeLine(repr(e))

        self.text = '$> '
        self.writeLine(self.text)

    def destroy(self):
        Clutter.main_quit()

    def onKeyPress(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        if event.key.keyval > 255:
            if event.key.keyval == 65293:  # enter
                self.newLine()
        else:
            pressed = chr(event.key.keyval)
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

            if (modControl and pressed == 'd'):
                print "Quitting"
                self.destroy()

            self.text += pressed
            self.clutterText.set_text(self.text)


def main():
    if DEBUG:
        Clutter.init(debugArgs)
    else:
        Clutter.init(sys.argv)
    app = GUI()
    Clutter.main()

if __name__ == "__main__":
    sys.exit(main())
