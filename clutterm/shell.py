import io
import os
import pty
import sys
import shlex
import fcntl
import struct
import termios
import logging
import select
from gi.repository import GObject
from subprocess import Popen
from threading import Thread
log = logging.getLogger('clutterm')


class ReaderAsync(Thread):
    def __init__(self, shell, callback, final_callback):
        self.shell = shell
        self.callback = callback
        self.final_callback = final_callback
        self.loop = True
        Thread.__init__(self)

    def run(self):
        while self.loop:
            log.debug('Waiting for select')
            select.select([self.shell.fd], [], [self.shell.fd])
            log.debug('Reading after select')
            read = self.shell.read()
            if read is None:
                log.info('Read None, breaking select loop.')
                break
            log.debug('Calling callback')

            def callback(*args):
                try:
                    self.callback(*args)
                except Exception:
                    log.exception('Exception on async callback')
                    self.loop = False
            GObject.idle_add(callback, read)
            log.debug('Callback called')

        log.info('ReaderAsync terminated, launching final callback')
        self.final_callback()


class Shell(object):

    def __init__(self, options, rows=40, cols=100, end_callback=None):
        self.rows = rows
        self.cols = cols
        self.end_callback = end_callback
        self.shell = options.shell or os.getenv('SHELL')
        self.still_alive = True
        self.fork()

    def read(self):
        try:
            read = self.reader.read()
        except IOError:
            log.exception('Got an IO')
            if self.end_callback:
                self.end_callback()
            self.still_alive = False
            return
        if read:
            log.info('R<%r>' % read)

        return read

    def write(self, text):
        log.info('W     <%r>' % text)
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        self.writer.write(text)
        self.writer.flush()

    def resize(self, cols, rows):
        self.cols = cols
        self.rows = rows
        s = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, s)

    def fork(self):
        pid, fd = pty.fork()
        if pid == 0:
            # Child
            try:
                fd_list = [int(i) for i in os.listdir('/proc/self/fd')]
            except OSError:
                fd_list = xrange(256)
            # Close all file descriptors other than
            # stdin, stdout, and stderr (0, 1, 2)
            for i in [i for i in fd_list if i > 2]:
                try:
                    os.close(i)
                except OSError:
                    pass
            self.env = os.environ
            self.env["TERM"] = "xterm"
            self.env["COLORTERM"] = "clutterm"
            command = shlex.split(self.shell)
            self.env["SHELL"] = command[0]
            p = Popen(command, env=self.env)
            p.wait()
            log.info('Exiting...')
            sys.exit(0)
        else:
            # Parent
            log.debug('pty forked pid: %d fd: %d' % (pid, fd))
            fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)

            # Set the size of the terminal window:
            s = struct.pack("HHHH", self.rows, self.cols, 0, 0)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, s)

            self.fd = fd
            self.pid = pid

            self.reader = io.open(
                self.fd,
                'rt',
                buffering=1024,
                newline="",
                encoding='UTF-8',
                closefd=False,
                errors='handle_special'
            )
            self.writer = io.open(
                self.fd,
                'wt',
                buffering=1024,
                newline="",
                encoding='UTF-8',
                closefd=False
            )

    def quit(self):
        if self.still_alive:
            self.write('')
