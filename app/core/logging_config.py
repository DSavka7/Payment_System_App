import logging
import sys


def setup_logging() -> None:
    fmt = "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt=date_fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)