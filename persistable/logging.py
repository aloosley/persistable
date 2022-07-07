import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(
    name: str,
    file_loc: Optional[Path],
    console_level: Optional[int] = logging.DEBUG,
    file_level: Optional[int] = logging.DEBUG,
    format_str: str = "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
    adapt_from_logger: Optional[logging.Logger] = None,
) -> logging.Logger:
    """Get logger utiltity.

    ToDo - clean up using a builder pattern.

    has defaults for everything. just enter
    >>> logger = get_logger(
    >>>     name="Package", file_loc=Path("path/to/log_files/"), console_level=logging.INFO, file_level=logging.DEBUG
    >>> )
    if you want to deactivate the console_level logger (on by default) enter:
    >>> logger = get_logger(
    >>>     name="Package", file_loc=Path("path/to/log_files/"), console_level=None, file_level=logging.DEBUG
    >>> )
    """
    # default values:
    formatter = logging.Formatter(format_str)

    logger: logging.Logger
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

    if file_loc is not None:
        if file_level is None:
            file_level = logging.DEBUG

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
