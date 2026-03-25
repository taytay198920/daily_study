# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : handle_log.py


import sys
import logging
from lib.handle_path import log_path


def init_logger():
    with open(log_path, 'w'):
        pass

    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # log to screen
    screen_handler = logging.StreamHandler(sys.stdout)
    screen_handler.setFormatter(formatter)
    screen_handler.setLevel(logging.DEBUG)
    logger.addHandler(screen_handler)
    # log to file
    file_handler = logging.FileHandler(filename=log_path, mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    return logger

log = init_logger()
