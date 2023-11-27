import os
import re
import sys
from log_config import setup_logger

logger = setup_logger(__file__)

# Approved values
approved_values = {
    "Collection": "JPC",
    "MediaType": "AV",
    "FileExtension": "mkv"
}

def is_valid_filename(filename):
    # Define the regular expression pattern
    pattern = r'^{Collection}_{MediaType}_\d{{5}}\.{FileExtension}$'.format(**approved_values)
    
    # Check if the filename matches the pattern
    if re.match(pattern, filename, re.IGNORECASE):
        logger.debug(f"The file name '{filename}' is valid.")
    else:
        logger.debug(f"The file name '{filename}' does not match the naming convention.")

def validate_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        if is_valid_filename(filename):
            logger.debug(f"The file name '{filename}' is valid.")
        else:
            logger.debug(f"The file name '{filename}' does not match the naming convention.")

if sys.argv[0] == __file__:
    logger.debug('A debug message from filename_check.py')
    if len(sys.argv) != 2:
        print("Usage: python script-name.py /path/to/your/directory")
    else:
        directory_path = sys.argv[1]
        validate_files_in_directory(directory_path)
        