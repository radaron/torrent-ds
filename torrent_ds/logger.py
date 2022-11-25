import logging


def init_logger():
    syslog = logging.handlers.SysLogHandler(address="/dev/log")
    syslog.setFormatter(logging.Formatter('%(name)s: %(levelname)s %(message)s'))
    logger = logging.getLogger("torrent-ds")
    logger.addHandler(syslog)
    logger.setLevel(logging.INFO)
    logger.info("Logging was initialized.")
