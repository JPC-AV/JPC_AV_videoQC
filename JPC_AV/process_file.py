#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import logging
import yaml
import csv
from datetime import datetime
from log_setup import logger, console_handler
from deps_setup import required_commands, check_external_dependency, check_py_version
from find_config import config_path, command_config
from mediainfo_check import parse_mediainfo
from exiftool_check import parse_exiftool
from ffprobe_check import parse_ffprobe

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
        logger.debug(f"The file name '{filename}' is valid.")
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
    
    directory_path = os.path.dirname(video_path)

    directory_name = os.path.basename(directory_path)

    if video_name == directory_name:
        logger.debug(f'Video ID matches directory name')
    else:
        logger.critical(f'Video ID, {video_name}, does not match directory name: {directory_name}')
    
    logger.debug(f'Metadata files will be written to {directory_path}')

    return directory_path

def run_command(command, input_path, output_type, output_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    full_command = f"{command} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'running command: {full_command}')
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

def write_to_csv(diff_list, tool_name, config, writer):
    for diff in diff_list:
        # Split the difference string into lines
        lines = diff.strip().split('\n')
        
        # Iterate through the rest of the lines to find metadata field, expected, and actual values
        for line in lines:
            if line.startswith('\tExpected:'):
                expected_value = line.split(': ')[1].strip()
            elif line.startswith('\tActual:'):
                actual_value = line.split(': ')[1].strip()
            else:
                metadata_field = line.strip()
        
        if config == 'yes':
            # Write data to CSV file
            writer.writerow({
                'Metadata Tool': tool_name,
                'Metadata Field': metadata_field,
                'Expected Value': expected_value,
                'Actual Value': actual_value
            })

        # Log the difference
        logger.critical(f'\n\t{diff}')

def main():
    '''
    process_file.py takes 1 input file as an argument, like this:
    python process_file.py <input_file.mkv>
    it confirms the file is valid, creates an output directory, generates metadata on the file then checks it against expected values.
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
    
    # Create a directory with the same name as the video file
    destination_directory = check_directory(video_path)
    
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    if command_config.command_dict['tools']['mediaconch']['run_mediaconch'] == 'yes':
        mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
        run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

        # open the mediaconch csv ouput and check for the word 'fail'
        with open(mediaconch_output_path) as mc_file:
            if 'fail' in mc_file.read():
                logger.critical('MediaConch policy failed') 

    # Run exif, mediainfo and ffprobe using the 'run_command' function
    if command_config.command_dict['tools']['exiftool']['run_exiftool'] == 'yes':
        exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
        run_command('exiftool', video_path, '>', exiftool_output_path)

    if command_config.command_dict['tools']['mediainfo']['run_mediainfo'] == 'yes':
        mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
        run_command('mediainfo -f', video_path, '>', mediainfo_output_path)

    if command_config.command_dict['tools']['ffprobe']['run_ffprobe'] == 'yes':
        ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
        run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, '>', ffprobe_output_path)

    if command_config.command_dict['tools']['qctools']['run_qctools'] == 'yes':
        qctools_ext = command_config.command_dict['outputs']['qctools_ext']
        qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
        run_command('qcli -i', video_path, '-o', qctools_output_path)

    logger.info(f'Processing complete. Output files saved in the directory: {destination_directory}')

    # Create CSV for storing differences between expected metadata values and actual values
    csv_name = video_id + '_' + 'metadata_difference'
    csv_path = destination_directory + "/" + csv_name + ".csv"
    if os.path.exists(csv_path):
        # if CSV file already exists, append a timestamp to the new csv_name
        timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
        csv_name += '_' + timestamp
        csv_path = destination_directory + "/" + csv_name + ".csv"
    
    csv_config = command_config.command_dict['outputs']['difference_csv']

    
    # Open CSV file in write mode
    with open(csv_path, 'w', newline='') as diffs_csv:
        # Define CSV header
        fieldnames = ['Metadata Tool', 'Metadata Field', 'Expected Value', 'Actual Value']
        writer = csv.DictWriter(diffs_csv, fieldnames=fieldnames)
        
        # Write header to CSV file
        writer.writeheader()
        
        if command_config.command_dict['tools']['exiftool']['check_exiftool'] == 'yes':
            # If check_exfitool is set to 'yes' in command_config.yaml then
            exiftool_differences = parse_exiftool(exiftool_output_path)
            # Run parse functions defined in the '_check.py' scripts
            write_to_csv(exiftool_differences, 'exiftool', csv_config, writer)
            # and if actual values are different from expected values, write differences to CSV and to log

        if command_config.command_dict['tools']['mediainfo']['check_mediainfo'] == 'yes':
            # If check_mediainfo is set to 'yes' in command_config.yaml then
            mediainfo_differences = parse_mediainfo(mediainfo_output_path)
            # Run parse functions defined in the '_check.py' scripts
            write_to_csv(mediainfo_differences, 'mediainfo', csv_config, writer)
            # and if actual values are different from expected values, write differences to CSV and to log
    
        if command_config.command_dict['tools']['ffprobe']['check_ffprobe'] == 'yes':
             # If check_exfitool is set to 'yes' in command_config.yaml then
            ffprobe_differences = parse_ffprobe(ffprobe_output_path)
            # Run parse functions defined in the '_check.py' scripts
            write_to_csv(ffprobe_differences, 'ffprobe', csv_config, writer)
            # and if actual values are different from expected values, write differences to CSV and to log

    # Open CSV and read the content to variable 'rows'
    with open(csv_path, 'r', newline='') as check_csv:
        reader = csv.reader(check_csv)
        rows = list(reader)  # Read the CSV file
    
    # If CSV file exists, and has only 1 row, then it only contains the header. 
    # CSV will only contain header if there are no differences, or if difference_csv is set to 'no' in the command_config.yaml 
    if os.path.exists(csv_path):
        if len(rows) == 1:
            os.remove(csv_path)

if __name__ == "__main__":
    main()
