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
import argparse
import time
from art import *
from datetime import datetime
from log_setup import logger, console_handler
from deps_setup import required_commands, check_external_dependency, check_py_version
from find_config import config_path, command_config
from fixity_check import check_fixity, output_fixity
from filename_check import check_filenames
from mediainfo_check import parse_mediainfo
from exiftool_check import parse_exiftool
from ffprobe_check import parse_ffprobe
from embed_fixity import extract_tags, extract_hashes, embed_fixity, validate_embedded_md5
from yaml_profiles import apply_profile, update_config, profile_step1, profile_step2, JPC_AV_SVHS, bowser_filename, JPCAV_filename
from make_access import make_access_file

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

def check_directory(source_directory, video_id):
    
    # Assuming DigitalGeneration is always prefixed with an underscore and is the last part before the file extension
    base_video_id = video_id.rsplit('_', 1)[0]  # Splits off the DigitalGeneration part

    directory_name = os.path.basename(source_directory)
    
 # Check if the directory name starts with the base_video_id string
    if directory_name.startswith(base_video_id):
        logger.info(f'\nDirectory name "{directory_name}" correctly starts with "{base_video_id}".\n')
    else:
        logger.critical(f'Directory name "{directory_name}" does not correctly start with the expected "{base_video_id}" derived from the video ID "{video_id}".')
    
def make_qc_output_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    destination_directory = os.path.join(source_directory, f'{video_id}_qc_metadata')

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)
    
    logger.debug(f'Metadata files will be written to {destination_directory}')

    return destination_directory

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
        logger.critical(f'\nPolicy file not found: {policy_file}')
    else:
        logger.debug(f'\nUsing MediaConch policy {policy_file}')
    
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

def find_mkv(source_directory):
    # Create empty list to store any found mkv files
    found_mkvs = []
    for filename in os.listdir(source_directory):
        if filename.lower().endswith('.mkv'):
            if 'qctools' not in filename.lower():
                found_mkvs.append(filename)
    # check if found_mkvs is more than one
    if found_mkvs:
        if len(found_mkvs) == 1:
            video_path = os.path.join(source_directory, found_mkvs[0])
            logger.info(f'\nInput video file found: {video_path}')
        else:
            logger.critical(f'\nMore than 1 mkv found in {source_directory}: {found_mkvs}')
            sys.exit(1)
    else:
        logger.critical("Error: No mkv video file found in the directory.")
        sys.exit(1)
    
    return video_path

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process video file with optional settings")
    parser.add_argument("paths", nargs='+', help="Path to the input -f: video file(s) or -d: directory(ies)")
    parser.add_argument("--profile", choices=["step1", "step2"], help="Select processing profile (step1 or step2)")
    parser.add_argument("-sn","--signalflow", choices=["JPC_AV_SVHS"], help="Select signal flow config type (JPC_AV_SVHS)")
    parser.add_argument("-fn","--filename", choices=["jpc", "bowser"], help="Select file name config type (jpc or bowser)")
    parser.add_argument("-d", "--directory", action="store_true", help="Flag to indicate input is a directory")
    parser.add_argument("-f", "--file", action="store_true", help="Flag to indicate input is a video file")

    args = parser.parse_args()

    input_paths = args.paths
    source_directories = []

    for input_path in input_paths:
        if args.file:
            if not os.path.isfile(input_path):
                logger.critical(f"Error: {input_path} is not a valid file.")
                sys.exit(1)
            source_directories.append(os.path.dirname(input_path))
            logger.info(f'Input directory found: {(os.path.dirname(input_path))}')
        else:
            if not os.path.isdir(input_path):
                logger.critical(f"Error: {input_path} is not a valid directory.")
                sys.exit(1)
            source_directories.append(input_path)
            logger.info(f'Input directory found: {input_path}')

    selected_profile = None
    if args.profile:
        if args.profile == "step1":
            selected_profile = profile_step1
        elif args.profile == "step2":
            selected_profile = profile_step2

    sn_config_changes = None
    if args.signalflow:
        if args.signalflow == "JPC_AV_SVHS":
            sn_config_changes = JPC_AV_SVHS
    
    fn_config_changes = None
    if args.filename:
        if args.filename == "jpc":
            fn_config_changes = JPCAV_filename
        elif args.filename =="bowser":
            fn_config_changes = bowser_filename

    return source_directories, selected_profile, sn_config_changes, fn_config_changes

def main():
    '''
    process_file.py takes 1 input file or directory as an argument, like this:
    python process_file.py <input_directory> (or -f <input_file.mkv>)
    it confirms the file is valid, generates metadata on the file, then checks it against expected values.
    '''

    source_directories, selected_profile, sn_config_changes, fn_config_changes = parse_arguments()

    check_py_version()
    
    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)
    
    if selected_profile:
        apply_profile(command_config, selected_profile)

    if sn_config_changes:
        update_config(config_path, 'ffmpeg_values.format.tags.ENCODER_SETTINGS', sn_config_changes)

    if fn_config_changes:
        update_config(config_path, 'filename_values', fn_config_changes)

    check_filenames(source_directories)

    overall_start_time = time.time()
    
    for source_directory in source_directories:
        dir_start_time = time.time()
        video_path = find_mkv(source_directory)

        tape_icon = art('cassette1')

        print(f'\n{tape_icon} {tape_icon} {tape_icon}')
    
        logger.warning(f'\nNow processing {video_path}')
        
        # outputs video_id (i.e. 'JPC_AV_05000')
        video_id = os.path.splitext(os.path.basename(video_path))[0]

        # Check to confirm directory is the same name as the video file name
        check_directory(source_directory, video_id)

        # Create 'destination directory' for qc outputs
        destination_directory = make_qc_output_dir(source_directory, video_id)

        # Moves vrecord files to subdirectory  
        move_vrec_files(source_directory, video_id)

        # Embed stream md5 hashes into MKV tags 
        if command_config.command_dict['outputs']['fixity']['embed_stream_fixity'] == 'yes':
            existing_tags = extract_tags(video_path)
            existing_video_hash, existing_audio_hash = extract_hashes(existing_tags)
            # Check if VIDEO_STREAM_HASH and AUDIO_STREAM_HASH MKV tags exists
            if existing_video_hash is None or existing_audio_hash is None :
                embed_fixity(video_path)
            else:
                logger.critical(f"Existing stream hashes found!")
                if command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'yes':
                    embed_fixity(video_path)
                elif command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'no':
                    logger.debug(f'Not writing stream hashes to MKV')
                elif command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'ask me':
                # User input for handling existing stream hashes
                # Directly lifted from this tutorial: https://stackabuse.com/bytes/handling-yes-no-user-input-in-python/
                    while True:
                        user_input = input("Do you want to overwrite existing stream hashes? (yes/no): ")
                        if user_input.lower() in ["yes", "y"]:
                            embed_fixity(video_path)
                            break
                        elif user_input.lower() in ["no", "n"]:
                            logger.debug(f'Not writing stream hashes to MKV')
                            break
                        else:
                            print("Invalid input. Please enter yes/no.")
                
        
        # Validate stream hashes
        if command_config.command_dict['outputs']['fixity']['check_stream_fixity'] == 'yes':
            validate_embedded_md5(video_path)
        
        # Initialize md5_checksum variable, so if it is not assigned in output_fixity, it is 'None' if run in check_fixity
        md5_checksum = None 

        # Create checksum for video file output results to '{video_id}_YYYY_MM_DD_fixity.txt' 
        if command_config.command_dict['outputs']['fixity']['output_fixity'] == 'yes':
            md5_checksum = output_fixity(source_directory, video_path)
        
        # Search for file with the suffix '_checksums.md5', verify stored checksum, and write result to '{video_id}_YYYY_MM_DD_fixity_check.txt' 
        if command_config.command_dict['outputs']['fixity']['check_fixity'] == 'yes':
            check_fixity(source_directory, video_id, actual_checksum=md5_checksum)
        
        # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
        if command_config.command_dict['tools']['mediaconch']['run_mediaconch'] == 'yes':
            mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
            run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

            # open the mediaconch csv ouput and check for the word 'fail'
            with open(mediaconch_output_path, 'r', newline='') as mc_file:
                reader = csv.reader(mc_file)
                mc_header = next(reader)  # Get the header row
                mc_values = next(reader)  # Get the values row

                 # Initialize a flag to track if any failures are found
                found_failures = False
                
                for mc_field, mc_value in zip(mc_header, mc_values):
                    if mc_value == "fail":
                        # If this is the first failure, print the initial message
                        if not found_failures:
                            logger.critical("\nMediaConch policy failed:")
                            found_failures = True
                            
                        # Print the field and value for the failed entry
                        logger.critical(f"{mc_field}: {mc_value}")

        # Run exiftool, mediainfo and ffprobe using the 'run_command' function
        exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
        if command_config.command_dict['tools']['exiftool']['run_exiftool'] == 'yes':
            run_command('exiftool', video_path, '>', exiftool_output_path)

        if command_config.command_dict['tools']['exiftool']['check_exiftool'] == 'yes':
            # If check_exfitool is set to 'yes' in command_config.yaml then
            parse_exiftool(exiftool_output_path)
            # Run parse functions defined in the '_check.py' scripts

        mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
        if command_config.command_dict['tools']['mediainfo']['run_mediainfo'] == 'yes':
            run_command('mediainfo -f', video_path, '>', mediainfo_output_path)
        
        if command_config.command_dict['tools']['mediainfo']['check_mediainfo'] == 'yes':
            # If check_mediainfo is set to 'yes' in command_config.yaml then
            parse_mediainfo(mediainfo_output_path)
            # Run parse functions defined in the '_check.py' scripts

        ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
        if command_config.command_dict['tools']['ffprobe']['run_ffprobe'] == 'yes':
            run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, '>', ffprobe_output_path)

        if command_config.command_dict['tools']['ffprobe']['check_ffprobe'] == 'yes':
            # If check_exfitool is set to 'yes' in command_config.yaml then
            parse_ffprobe(ffprobe_output_path)
            # Run parse functions defined in the '_check.py' scripts

        if command_config.command_dict['tools']['qctools']['run_qctools'] == 'yes':
            qctools_ext = command_config.command_dict['outputs']['qctools_ext']
            qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
            run_command('qcli -i', video_path, '-o', qctools_output_path)

        access_output_path = os.path.join(source_directory, f'{video_id}_access.mp4')
        if command_config.command_dict['outputs']['access_file'] == 'yes':
            make_access_file(video_path, access_output_path)
            
        logger.debug(f'\nPlease note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!')
        
        ascii_video_id = text2art(video_id, font='small')

        logger.warning(f'\nProcessing complete:\n{ascii_video_id}')
        logger.info(f'\nOutput files saved in the directory: {destination_directory}')

        dir_end_time = time.time()
        dir_total_time = dir_end_time - dir_start_time
        formatted_total_time = time.strftime("%H:%M:%S", time.gmtime(dir_total_time))
        #print(f"Process time for {video_id}: time start: {dir_start_time:%Y-%m-%d %H:%M:%S}")

        logger.info(f'\nProcess time for {video_id}: \ntime start: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dir_start_time))}; time end: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dir_end_time))}; \ntotal time: {formatted_total_time}')
        
        print(f'\n{tape_icon} {tape_icon} {tape_icon}')

        time.sleep(1)

    nmaahc_icon = text2art("nmaahc",font='alligator3')
    print(f'\n{nmaahc_icon}')
    
    logger.warning(f'\n\nAll files processed!')
    overall_end_time = time.time()
    overall_total_time = overall_end_time - overall_start_time
    formatted_overall_time = time.strftime("%H:%M:%S", time.gmtime(overall_total_time))
    logger.info(f"\nOverall processing time for all directories: {formatted_overall_time}\n")

if __name__ == "__main__":
    main()
