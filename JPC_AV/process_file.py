#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import logging
import yaml
from log_setup import logger
from find_config import config_path
from mediainfo_check import parse_mediainfo
from exiftool_check import parse_exiftool
from ffprobe_check import parse_ffprobe

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

def create_directory(video_path):
    '''
    defines the name of the output directory as the file name of the input video file
    checks for output path - the parent directory of the output directory - set in config/config.yaml 
    if the output path is not set, defaults to a directory called 'output' in the root dir of the scripts
    '''
    
    directory_name = os.path.splitext(os.path.basename(video_path))[0]

    if config_path.config_dict['output_path'] != None:
            output_path = config_path.config_dict['output_path']
            directory_path = os.path.join(output_path, directory_name)
    else:
        output_path = os.path.join(config_path.root_dir, 'output')
        logger.debug(f'No output_path found in {config_path.config_yml}, using default {output_path}')
        directory_path = os.path.join(output_path, directory_name)

    # if the output directory does not exist, create it
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    logger.debug(f'Video file will be moved to {directory_path}')

    return directory_path

def move_video_file(video_path, destination_directory):
    '''
    Move video file to output directory
    '''

    video_name = os.path.basename(video_path)
    destination_path = os.path.join(destination_directory, video_name)
    logger.debug(f'{video_name} moved to {destination_directory}')
    os.rename(video_path, destination_path)

def run_command(command, input_path, output_path):
    '''
    Run a shell command with 3 variables: command name, path to the input file, path to the output file
    '''

    full_command = f"{command} {input_path} > {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'running command: {full_command}')

# Mediaconch needs its own function, because the command's flags and multiple inputs don't conform to the simple 3 part structure of the other commands
def run_mediaconch_command(command, input_path, output_type, output_path):
    '''
    This function runs a shell command that takes 4 variables: 
    command name, path to the input file, the output type (currently hardcoded to -oc for csv), and path to the output file
    Finds policy path specified in config/config.yaml
    Currently defaults to config/JPC_AV_NTSC_MKV_2023-11-21.xml
    '''

    policy_file = config_path.config_dict['mediaconch_policy']
    policy_path = os.path.join(config_path.config_dir, policy_file)
    
    if not os.path.exists(policy_path):
        logger.critical(f'Policy file not found: {policy_file}')
    else:
        logger.debug(f'Using MediaConch policy {policy_file}')
    
    full_command = f"{command} {policy_path} {input_path} {output_type} {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'running command: {full_command}')

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

    video_name = os.path.basename(video_path)
    
    is_valid_filename(video_name)

    video_id = os.path.splitext(os.path.basename(video_name))[0]
    
    # Create a directory with the same name as the video file
    destination_directory = create_directory(video_path)
    
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
    run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

    # open the mediaconch csv ouput and check for the word 'fail'
    with open(mediaconch_output_path) as mc_file:
        if 'fail' in mc_file.read():
            logger.critical('MediaConch policy failed') 

    # Run exif, mediainfo and ffprobe using the 'run_command' function
    exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
    run_command('exiftool', video_path, exiftool_output_path)

    mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
    run_command('mediainfo -f', video_path, mediainfo_output_path)

    ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
    run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, ffprobe_output_path)

    # Move the video file into the created directory
    move_video_file(video_path, destination_directory)

    logger.info(f'Processing complete. Output files saved in the directory: {destination_directory}')

    # Run parse functions defined in the '_check.py' scripts
    parse_mediainfo(mediainfo_output_path)

    parse_exiftool(exiftool_output_path)

    parse_ffprobe(ffprobe_output_path)

if __name__ == "__main__":
    main()
