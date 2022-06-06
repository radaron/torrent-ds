import logging
from logging.handlers import RotatingFileHandler


def init_logger(name, log_path):
    log_formatter = logging.Formatter("%(asctime)s  %(module)s:%(funcName)s "
                                      "[%(levelname)s] %(message)s")

    my_handler = RotatingFileHandler(log_path, mode='a', maxBytes=5*1024*1024,
                                     backupCount=4, encoding=None, delay=0)

    my_handler.setFormatter(log_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(my_handler)
    logger.setLevel(logging.INFO)

    logger.info("Logging was initialized.")
