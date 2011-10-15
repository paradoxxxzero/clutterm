from attest import Tests, assert_hook
from clutterm.shell import Shell
import os
sh = Tests()


@sh.test
def shell():
    shell = Shell()
    assert shell.shell == os.getenv('SHELL')
