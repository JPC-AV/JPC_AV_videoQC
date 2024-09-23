import os
import re
import sys
import logging
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config


def is_valid_filename(video_filename):
    '''
    Locates approved values for the file name, stored in key:value pairs under 'filename_values' in config/config.yaml
    The file name pattern is in 5 sections: Collection, ObjectID, Media type, Digital generation, and file extension
    Approved values for each of these sections are stored in config/config.yaml
    '''
    valid_filename = False
    
    # Reads filename_values from config.yaml into dictionary approved_values
    approved_values = config_path.config_dict['filename_values']

    # Get only the base filename (not the full path)
    base_filename = os.path.basename(video_filename)

    # Then piece the parts of the approved values into the file name pattern that the input video will be tested against
    # The pattern has to account for the last value in the approved_values dict being a file extension instead of a file name "field"
    pattern = r'^{0}_{1}_{2}\.{3}$'.format(
        re.escape(approved_values['Collection']),
        re.escape(approved_values['MediaType']),
        approved_values['ObjectID'],  # ObjectID is already a regex pattern, so no escaping here
        re.escape(approved_values['FileExtension'])
    )
    
    # Check if the filename matches the pattern
    if re.match(pattern, base_filename, re.IGNORECASE):
        logger.debug(f"The file name '{base_filename}' is valid.\n")
        valid_filename = True
    else:
        logger.critical(f"The file name '{base_filename}' is not valid.\n")
        valid_filename = False

    return valid_filename


if sys.argv[0] == __file__:
    if len(sys.argv) != 2:
        print("Usage: python filename_check.py /path/to/your/directory")
    else:
        video_path = sys.argv[1]
        valid_filename = is_valid_filename(video_path)
