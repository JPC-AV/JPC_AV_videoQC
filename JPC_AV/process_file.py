#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import logging
import yaml
from log_setup import logger
from deps_setup import required_commands, check_external_dependency
from find_config import config_path
from mediainfo_check import parse_mediainfo
from exiftool_check import parse_exiftool
from ffprobe_check import parse_ffprobe

def is_valid_filename(filename):
    approved_values = config_path.config_dict['filename_values']
    
    # Define the regular expression pattern
    pattern = r'^{Collection}_{MediaType}_\d{{5}}\.{FileExtension}$'.format(**approved_values)
    
    # Check if the filename matches the pattern
    if re.match(pattern, filename, re.IGNORECASE):
        logger.debug(f"The file name '{filename}' is valid.")
    else:
        logger.critical(f"The file name '{filename}' does not match the naming convention. Exiting script!")
        sys.exit()

def create_directory(video_path):
    directory_name = os.path.splitext(os.path.basename(video_path))[0]
    if config_path.config_dict['output_path'] != None:
            output_path = config_path.config_dict['output_path']
            directory_path = os.path.join(output_path, directory_name)
    else:
        output_path = os.path.join(config_path.root_dir, 'output')
        logger.debug(f'No output_path found in {config_path.config_yml}, using default {output_path}')
        directory_path = os.path.join(output_path, directory_name)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    logger.debug(f'Video file will be moved to {directory_path}')

    return directory_path

def move_video_file(video_path, destination_directory):
    video_name = os.path.basename(video_path)
    destination_path = os.path.join(destination_directory, video_name)
    logger.debug(f'{video_name} moved to {destination_directory}')
    os.rename(video_path, destination_path)

def run_command(command, input_path, output_path):
    full_command = f"{command} {input_path} > {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'running commnad: {full_command}')

def run_mediaconch_command(command, input_path, output_type, output_path):
    policy_file = config_path.config_dict['mediaconch_policy']
    policy_path = os.path.join(config_path.config_dir, policy_file)
    
    if not os.path.exists(policy_path):
        logger.critical(f'Policy file not found: {policy_file}')
    else:
        logger.debug(f'Using MediaConch policy {policy_file}')
    
    full_command = f"{command} {policy_path} {input_path} {output_type} {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'running commnad: {full_command}')

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: {video_path} is not a valid file.")
        sys.exit(1)

    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)
    
    video_name = os.path.basename(video_path)
    
    is_valid_filename(video_name)

    video_id = os.path.splitext(os.path.basename(video_name))[0]
    
    # Create a directory with the same name as the video file
    destination_directory = create_directory(video_path)
    
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
    run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

    with open(mediaconch_output_path) as mc_file:
        if 'fail' in mc_file.read():
            logger.critical('MediaConch policy failed') 

    exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
    run_command('exiftool', video_path, exiftool_output_path)

    mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
    run_command('mediainfo -f', video_path, mediainfo_output_path)

    ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
    run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, ffprobe_output_path)

    # Move the video file into the created directory
    move_video_file(video_path, destination_directory)

    logger.info(f'Processing complete. Output files saved in the directory: {destination_directory}')

    parse_mediainfo(mediainfo_output_path)

    parse_exiftool(exiftool_output_path)

    parse_ffprobe(ffprobe_output_path)

if __name__ == "__main__":
    main()
