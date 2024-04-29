import os
import re
import sys
import logging
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config

def find_all_filenames(source_directory, found_mkvs):
    # Create empty list to store any found mkv files
    for filename in os.listdir(source_directory):
        if filename.lower().endswith('.mkv') and 'qctools' not in filename.lower():
            found_mkvs.append(os.path.basename(filename))
    # check if found_mkvs is empty
    if not found_mkvs:
        logger.critical("Error: No mkv video files found in the directory.")
        sys.exit(1)
    
    return found_mkvs

def is_valid_filename(video_filename, failed_mkvs):
    '''
    Locates approved values for the file name, stored in key:value pairs under 'filename_values' in config/config.yaml
    The file name pattern is in 3 sections: Collection, Media type, and file extension
    Approved values for each of these sections is stored in config/config.yaml
    '''
    approved_values = config_path.config_dict['filename_values']
    
    pattern = r'^{Collection}_{MediaType}_\d{{5}}\.{FileExtension}$'.format(**approved_values)
    
    # Check if the filename matches the pattern
    if re.match(pattern, video_filename, re.IGNORECASE):
        logger.debug(f"\nThe file name '{video_filename}' is valid.")
    else:
        failed_mkvs.append(video_filename)

    return failed_mkvs

def check_filenames(source_directories):
    '''
    Runs 2 functions: find_all_filenames and is_valid_filename
    Takes all directories provided as arguments to the script, locates the MKV, and checks the file name against approved values.
    Approved values for each of section of the filename is stored in config/config.yaml
    '''
     
    found_mkvs = []
    failed_mkvs = []
    
    for source_directory in source_directories:

        found_mkvs = find_all_filenames(source_directory, found_mkvs )
            
    for video_filename in found_mkvs:
        # Confirms video filename matches convention
        failed_mkvs = is_valid_filename(video_filename, failed_mkvs)
    
    if failed_mkvs:
            logger.critical('The following MKVs do not match the file naming convention:')
            for failed_mkv in failed_mkvs:
                logger.critical(failed_mkv)
            sys.exit(1)

if sys.argv[0] == __file__:
    if len(sys.argv) != 2:
        print("Usage: python filename_check.py /path/to/your/directory")
    else:
        directory_path = sys.argv[1]
        found_mkvs = []
        failed_mkvs = []

        found_mkvs = find_all_filenames(directory_path)
                
        for video_filename in found_mkvs:
            # Confirms video filename matches convention
            failed_mkvs = is_valid_filename(video_filename)
        
        if failed_mkvs:
             print('The following MKVs do not match the file naming convention:')
             for failed_mkv in failed_mkvs:
                  print(failed_mkv)
             sys.exit(1)
        