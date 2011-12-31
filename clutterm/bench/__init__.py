import time


class Timer(object):
    def __enter__(self):
        self._start = time.time()

    def __exit__(self, type, value, traceback):
        self._finish = time.time()

    @property
    def time(self):
        return (self._finish - self._start) * 1000
