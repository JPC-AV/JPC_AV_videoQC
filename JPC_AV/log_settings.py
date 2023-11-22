#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging          # This loads the "logging" module, which handles logging very simply
import os               # This loads the "os" module, useful for dealing with filepaths
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

logDir = os.getcwd()   
logName = datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '_' + os.path.splitext(os.path.basename(__file__))[0]
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
logging_handler_out.setLevel(logging.WARNING)
logging_handler_out.setFormatter(logging.Formatter(STDOUT_FORMAT))
logger.addHandler(logging_handler_out)

# Logs
logger.debug('A debug message')
logger.info('An info message')
logger.warning('Something is not right.')
logger.error('A Major error has happened.')
logger.critical('Fatal error. Cannot continue')