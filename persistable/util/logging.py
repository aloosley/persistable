import logging
import sys
from pathlib import Path

DEFAULTLOGFOLDER = Path('.').absolute()

def get_logger(
        name, file_loc=None, console_level=logging.DEBUG, file_level=None, format_str=None, adapt_from_logger=None
):
    """ has defaults for everything. just enter
    >>> logger = get_logger("Package", console_level=logging.INFO, file_level=logging.DEBUG)
    if you want to deactivate the console_level logger (on by default) enter:
    >>> logger = get_logger("Package", console_level=None, file_level=logging.DEBUG)
    The ``file_level=None`` by default, however if you enter a ``file_loc`` then it automatically defaults to
    ``logging.DEBUG``
    """
    # default values:
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_str)
    if file_loc is not None and file_level is None:
        file_level = logging.DEBUG
    if file_level is not None and file_loc is None:
        file_loc = DEFAULTLOGFOLDER / (name + ".log")

    if adapt_from_logger:
        logger = adapt_from_logger
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # set it to lowest possible, this needs to be done for logging to happen at all

    if console_level is not None:
        no_handlers = True
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.setLevel(console_level)
                h.setFormatter(formatter)
                no_handlers = False
        if no_handlers:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(console_level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

    if file_level is not None:
        no_handlers = True
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler):
                h.setLevel(file_level)
                h.setFormatter(formatter)
                no_handlers = False
        if no_handlers:
            fh = logging.FileHandler(file_loc, encoding="utf-8")
            fh.setLevel(file_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger