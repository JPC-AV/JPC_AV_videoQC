#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import logging
import yaml
import csv
import shutil
from datetime import datetime
from log_setup import logger, console_handler
from deps_setup import required_commands, check_external_dependency, check_py_version
from find_config import config_path, command_config
from fixity_check import check_fixity, output_fixity
from mediainfo_check import parse_mediainfo
from exiftool_check import parse_exiftool
from ffprobe_check import parse_ffprobe
from embed_fixity import embed_fixity

# Read command_config.yaml and retrieve log level
log_level_str = command_config.command_dict['log_level']
# Match log level from command_config.yaml to logging command
log_level_mapping = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Set the console_handler log level, the color output to terminal, based on the mapping
if log_level_str in log_level_mapping:
    console_handler.setLevel(log_level_mapping[log_level_str])

def is_valid_filename(filename):
    '''
    Locates approved values for the file name, stored in key:value pairs under 'filename_values' in config/config.yaml
    The file name pattern is in 3 sections: Collection, Media type, and file extension
    Approved values for each of these sections is stored in config/config.yaml
    '''
    approved_values = config_path.config_dict['filename_values']
    
    pattern = r'^{Collection}_{MediaType}_\d{{5}}\.{FileExtension}$'.format(**approved_values)
    
    # Check if the filename matches the pattern
    if re.match(pattern, filename, re.IGNORECASE):
        logger.info(f"\nThe file name '{filename}' is valid.")
    else:
        logger.critical(f"The file name '{filename}' does not match the naming convention. Exiting script!")
        sys.exit()

def check_directory(video_path):
    '''
    defines the name of the output directory as the file name of the input video file
    checks for output path - the parent directory of the output directory - set in config/config.yaml 
    if the output path is not set, defaults to a directory called 'output' in the root dir of the scripts
    '''
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    source_path = os.path.dirname(video_path)
    directory_name = os.path.basename(source_path)

    if video_name == directory_name:
        logger.info(f'Video ID matches directory name\n')
    else:
        logger.critical(f'Video ID, {video_name}, does not match directory name: {directory_name}')
    
    directory_path = os.path.join(source_path, f'{video_name}_qc_metadata')

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    logger.debug(f'Metadata files will be written to {directory_path}')

    return directory_path

def run_command(command, input_path, output_type, output_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    full_command = f"{command} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'\nrunning command: {full_command}')
    subprocess.run(full_command, shell=True)

# Mediaconch needs its own function, because the command's flags and multiple inputs don't conform to the simple 3 part structure of the other commands
def run_mediaconch_command(command, input_path, output_type, output_path):
    '''
    This function runs a shell command that takes 4 variables: 
    command name, path to the input file, the output type (currently hardcoded to -oc for csv), and path to the output file
    Finds policy path specified in config/config.yaml
    Currently defaults to config/JPC_AV_NTSC_MKV_2023-11-21.xml
    '''

    policy_file = command_config.command_dict['tools']['mediaconch']['mediaconch_policy']
    policy_path = os.path.join(config_path.config_dir, policy_file)
    
    if not os.path.exists(policy_path):
        logger.critical(f'Policy file not found: {policy_file}')
    else:
        logger.debug(f'Using MediaConch policy {policy_file}')
    
    full_command = f"{command} {policy_path} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'running command: {full_command}')
    subprocess.run(full_command, shell=True)

def move_vrec_files(directory, video_id):
    vrecord_files_found = False

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if the file matches the naming convention
        if (
            os.path.isfile(file_path)
            and "JPC_AV_" in filename
            and filename.endswith(('_QC_output_graphs.jpeg', '_vrecord_input.log', '_capture_options.log', '.mkv.qctools.mkv', '.framemd5'))
        ):
            # Create the target directory if it doesn't exist
            vrecord_directory = os.path.join(directory, f'{video_id}_vrecord_metadata')
            os.makedirs(vrecord_directory, exist_ok=True)
            # Move the file to the target directory
            new_path = os.path.join(vrecord_directory, filename)
            shutil.move(file_path, new_path)
            #logger.debug(f'Moved vrecord file: {filename} to directory: {os.path.basename(vrecord_directory)}')
            vrecord_files_found = True
        
    # Check if any matching files were found to create the directory
    if vrecord_files_found:
        logger.debug(f"\nFiles generated by vrecord found. '{video_id}_vrecord_metadata' directory created and files moved.")
    else:
        logger.debug("\nNo vrecord files found.\n")

def main():
    '''
    process_file.py takes 1 input file as an argument, like this:
    python process_file.py <input_file.mkv>
    it confirms the file is valid generates metadata on the file then checks it against expected values.
    '''

    if len(sys.argv) != 2:
        print("Usage: python script.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: {video_path} is not a valid file.")
        sys.exit(1)

    check_py_version()
    
    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)
    
    video_name = os.path.basename(video_path)
    
    is_valid_filename(video_name)

    video_id = os.path.splitext(os.path.basename(video_name))[0]
    
    # Check to confirm directory is the same name as the video file name
    destination_directory = check_directory(video_path)
    source_directory = os.path.dirname(destination_directory)

    # Moves vrecord files to subdirectory  
    move_vrec_files(source_directory, video_id)
    
    # Initialize md5_checksum variable, so if it is not assigned in output_fixity, it is 'None' if run in check_fixity
    md5_checksum = None 

    # Create checksum for video file output results to '{video_id}_YYYY_MM_DD_fixity.txt' 
    if command_config.command_dict['outputs']['fixity']['output_fixity'] == 'yes':
        md5_checksum = output_fixity(destination_directory, video_path)
    
    # Search for file with the suffix '_checksums.md5', verify stored checksum, and write result to '{video_id}_YYYY_MM_DD_fixity_check.txt' 
    if command_config.command_dict['outputs']['fixity']['check_fixity'] == 'yes':
        check_fixity(source_directory, video_id, actual_checksum=md5_checksum)

    # Search for file with the suffix '_checksums.md5', verify stored checksum, and write result to '{video_id}_YYYY_MM_DD_fixity_check.txt' 
    if command_config.command_dict['outputs']['fixity']['embed_stream_fixity'] == 'yes':
        embed_fixity(video_path)
   
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    if command_config.command_dict['tools']['mediaconch']['run_mediaconch'] == 'yes':
        mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
        run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

        # open the mediaconch csv ouput and check for the word 'fail'
        with open(mediaconch_output_path) as mc_file:
            if 'fail' in mc_file.read():
                logger.critical('MediaConch policy failed') 

    # Run exiftool, mediainfo and ffprobe using the 'run_command' function
    if command_config.command_dict['tools']['exiftool']['run_exiftool'] == 'yes':
        exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
        run_command('exiftool', video_path, '>', exiftool_output_path)

    if command_config.command_dict['tools']['exiftool']['check_exiftool'] == 'yes':
        # If check_exfitool is set to 'yes' in command_config.yaml then
        parse_exiftool(exiftool_output_path)
        # Run parse functions defined in the '_check.py' scripts

    if command_config.command_dict['tools']['mediainfo']['run_mediainfo'] == 'yes':
        mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
        run_command('mediainfo -f', video_path, '>', mediainfo_output_path)
    
    if command_config.command_dict['tools']['mediainfo']['check_mediainfo'] == 'yes':
        # If check_mediainfo is set to 'yes' in command_config.yaml then
        parse_mediainfo(mediainfo_output_path)
        # Run parse functions defined in the '_check.py' scripts

    if command_config.command_dict['tools']['ffprobe']['run_ffprobe'] == 'yes':
        ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
        run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, '>', ffprobe_output_path)

    if command_config.command_dict['tools']['ffprobe']['check_ffprobe'] == 'yes':
        # If check_exfitool is set to 'yes' in command_config.yaml then
        parse_ffprobe(ffprobe_output_path)
        # Run parse functions defined in the '_check.py' scripts

    if command_config.command_dict['tools']['qctools']['run_qctools'] == 'yes':
        qctools_ext = command_config.command_dict['outputs']['qctools_ext']
        qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
        run_command('qcli -i', video_path, '-o', qctools_output_path)

    logger.debug(f'\nPlease note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!')
    
    logger.info(f'\nProcessing complete. Output files saved in the directory: {destination_directory}')

if __name__ == "__main__":
    main()
