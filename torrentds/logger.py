import logging
from logging.handlers import RotatingFileHandler

def init_logger(name, log_path):
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

    my_handler = RotatingFileHandler(log_path, mode='a', maxBytes=5*1024*1024, 
                                     backupCount=4, encoding=None, delay=0)
    
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)

    logger = logging.getLogger(name)
    logger.addHandler(my_handler)

