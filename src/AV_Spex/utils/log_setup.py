#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys
import colorlog
from datetime import datetime
from colorlog import ColoredFormatter
from pathlib import Path

def get_log_directory():
    """Determine the appropriate log directory based on how the app is running"""
    if getattr(sys, 'frozen', False):
        # If running as packaged app
        log_dir = os.path.join(str(Path.home()), 'Library', 'Logs', 'AVSpex')
    else:
        # If running from source
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        log_dir = os.path.join(root_dir, 'logs')
    
    # Add date subdirectory
    log_dir = os.path.join(log_dir, datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

# Much of this script is taken from the AMIA open source project loglog. More information here: https://github.com/amiaopensource/loglog

def setup_logger(): 
    # Assigns getLogger function from imported module, creates logger 
    logger = logging.getLogger()
    # Sets 'lowest' log level
    logger.setLevel(logging.DEBUG)

    # Establishes path to 'logs' directory
    log_dir = get_log_directory()
    log_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_AVSpex"
    log_path = os.path.join(log_dir, f"{log_name}.log")

    # Define log formats which will be used in 'formatter' for the 2 log handlers
    LOG_FORMAT = '%(asctime)s - %(levelname)s: %(message)s'
    STDOUT_FORMAT = '%(message)s' 

    ## This project uses 2 log handlers, one for the log file 'file_handler', and one for the terminal output 'console_handler' 
    # define file handler and set formatter
    file_handler = logging.FileHandler(log_path)
    formatter    = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    # set log level
    file_handler.setLevel(logging.DEBUG)
    # add file handler to logger
    logger.addHandler(file_handler)

    # define console_handler and set format for terminal output
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s' + STDOUT_FORMAT,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    # add console handler to logger
    logger.addHandler(console_handler)

    return logger


logger = setup_logger() 

# Example logs (only execute if this file is run directly, not imported)
if __name__ == "__main__":
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('Something is not right.')
    logger.error('A Major error has happened.')
    logger.critical('Fatal error. Cannot continue')