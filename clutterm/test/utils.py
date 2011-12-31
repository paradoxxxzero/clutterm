import logging


def activate_log(level=logging.debug):
    log = logging.getLogger('clutterm')
    handler = None
    try:
        from log_colorizer import make_colored_stream_handler
        handler = make_colored_stream_handler()
    except ImportError:
        handler = logging.StreamHandler()

    log.addHandler(handler)
    log.setLevel(level)
