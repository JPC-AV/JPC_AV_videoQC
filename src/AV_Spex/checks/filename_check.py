import os
import re
import sys
import logging
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config


def is_valid_filename(video_filename):
    '''
    Locates approved values for the file name, stored in key:value pairs under 'filename_values' in config/config.yaml.
    The file name pattern varies and is constructed dynamically depending on the provided config.
    '''
    valid_filename = False
    
    # Reads filename_values from config.yaml into dictionary approved_values
    approved_values = config_path.config_dict['filename_values']

    # Get only the base filename (not the full path)
    base_filename = os.path.basename(video_filename)

    # Build the dynamic regex pattern based on the keys in the config
    pattern_parts = [
        re.escape(approved_values['Collection']),
        re.escape(approved_values['MediaType']),
        approved_values['ObjectID']  # ObjectID can contain a regex, so no escaping
    ]
    
    # Check if 'DigitalGeneration' is part of the convention and include it in the pattern if present
    if 'DigitalGeneration' in approved_values:
        pattern_parts.append(re.escape(approved_values['DigitalGeneration']))
    
    # Append the file extension
    file_extension = re.escape(approved_values['FileExtension'])
    
    # Construct the complete pattern, joining the parts and accounting for the file extension
    pattern = r'^{0}\.{1}$'.format('_'.join(pattern_parts), file_extension)
    
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
