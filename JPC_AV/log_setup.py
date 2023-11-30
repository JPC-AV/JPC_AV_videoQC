#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging          
import os               
import sys
from datetime import datetime

# Much of this script is taken from the AMIA open source prokect loglog. More information here: https://github.com/amiaopensource/loglog

logger = logging.getLogger()

# logDir = os.getcwd()
root_dir = os.path.join(os.path.abspath(os.getcwd()))
logs_parent_dir = os.path.join(root_dir, 'logs')
log_dir_path = os.path.join(logs_parent_dir, datetime.now().strftime('%Y-%m-%d'))
if not os.path.exists(log_dir_path):
    os.makedirs(log_dir_path)
logDir = log_dir_path
logName = datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '_' + 'JPC_AV_log'
logPath = logDir + "/" + logName + ".log"  

LOG_FORMAT = '%(asctime)s - %(levelname)s: %(message)s'
STDOUT_FORMAT = '%(asctime)s - %(message)s' 

# set log level
logger.setLevel(logging.DEBUG)

# define file handler and set formatter
file_handler = logging.FileHandler(logPath)
formatter    = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)

logging_handler_out = logging.StreamHandler(sys.stdout)
logging_handler_out.setLevel(logging.DEBUG)
logging_handler_out.setFormatter(logging.Formatter(STDOUT_FORMAT))
logger.addHandler(logging_handler_out)

# Example logs (only execute if this file is run directly, not imported)
if __name__ == "__main__":
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('Something is not right.')
    logger.error('A Major error has happened.')
    logger.critical('Fatal error. Cannot continue')