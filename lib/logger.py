import logging
import os
import lib.conf as conf

PATH_TO_SCRIPT = conf.get_path_to_logger()

DEFAULT_PATH_HIGH = PATH_TO_SCRIPT + '/logs/error.log'
DEFAULT_PATH_LOW = PATH_TO_SCRIPT + '/logs/info.log'
print("PATH_HIGH ", DEFAULT_PATH_HIGH)
print("PATH LOW ", DEFAULT_PATH_LOW)
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
NOTSET = logging.NOTSET
logging.getLogger().setLevel(logging.DEBUG)


def get_logger(name):
    def check_and_create_logger_files(path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        try:
            open(path, 'r').close()
        except FileNotFoundError:
            open(path, 'w').close()

    level = conf.get_logging_level()

    check_and_create_logger_files(DEFAULT_PATH_HIGH)
    check_and_create_logger_files(DEFAULT_PATH_LOW)
    formatter = logging.Formatter('%(asctime)s, %(name)s, [%(levelname)s]: %(message)s')

    log = logging.getLogger(name)
    file_high_logging_handler = logging.FileHandler(DEFAULT_PATH_HIGH)
    file_high_logging_handler.setLevel(logging.ERROR)
    file_high_logging_handler.setFormatter(formatter)
    log.addHandler(file_high_logging_handler)
    if level == '1':
        file_low_logging_handler = logging.FileHandler(DEFAULT_PATH_LOW)
        file_low_logging_handler.setLevel(logging.INFO)
        file_low_logging_handler.setFormatter(formatter)
        log.addHandler(file_low_logging_handler)

    return log