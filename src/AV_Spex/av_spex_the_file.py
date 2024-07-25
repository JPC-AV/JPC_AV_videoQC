#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import logging
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import csv
import shutil
import argparse
import importlib.metadata
import time
from art import *
from datetime import datetime

from .utils.log_setup import logger
from .utils.deps_setup import required_commands, check_external_dependency, check_py_version
from .utils.find_config import config_path, command_config, yaml
from .utils.yaml_profiles import *
from .utils.generate_report import write_html_report
from .checks.fixity_check import check_fixity, output_fixity
from .checks.filename_check import check_filenames
from .checks.mediainfo_check import parse_mediainfo
from .checks.mediatrace_check import parse_mediatrace
from .checks.exiftool_check import parse_exiftool
from .checks.ffprobe_check import parse_ffprobe
from .checks.embed_fixity import extract_tags, extract_hashes, embed_fixity, validate_embedded_md5
from .checks.make_access import make_access_file
from .checks.qct_parse import run_qctparse

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

def make_report_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    report_directory = os.path.join(source_directory, f'{video_id}_report_csvs')

    if not os.path.exists(report_directory):
        os.makedirs(report_directory)
    
    logger.debug(f'\nReport files will be written to {report_directory}')

    return report_directory

def run_command(command, input_path, output_type, output_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    # Get the current PATH environment variable
    env = os.environ.copy()
    env['PATH'] = '/usr/local/bin:' + env.get('PATH', '')

    full_command = f"{command} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'\nRunning command: {full_command}')
    subprocess.run(full_command, shell=True, env=env)

def run_mediatrace_command(command, input_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    # Get the current PATH environment variable
    env = os.environ.copy()
    env['PATH'] = '/usr/local/bin:' + env.get('PATH', '')

    full_command = f"{command} \"{input_path}\" "

    logger.debug(f'\nRunning mediainfo to generate MediaTrace XML: {full_command}')
    output = subprocess.run(full_command, shell=True, capture_output=True)

    return output

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

    logger.debug(f'\nRunning command: {full_command}')
    subprocess.run(full_command, shell=True)

def move_vrec_files(directory, video_id):
    vrecord_files_found = False

    # Create the target directory path
    vrecord_directory = os.path.join(directory, f'{video_id}_vrecord_metadata')

    # Check if the vrecord directory already exists and contains the expected files
    if os.path.exists(vrecord_directory):
        expected_files = [
            '_QC_output_graphs.jpeg',
            '_vrecord_input.log',
            '_capture_options.log',
            '.mkv.qctools.mkv',
            '.framemd5'
        ]
    
        # Check if at least one expected file is in the vrecord directory
        if any(filename.endswith(ext) for ext in expected_files for filename in os.listdir(vrecord_directory)):
            logger.debug(f"\nExisting vrecord files found in {os.path.basename(directory)}/{os.path.basename(vrecord_directory)}\n")
            return

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
        logger.debug("\nNo new vrecord files found.\n")

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

def write_to_csv(diff_dict, tool_name, writer):
     for key, values in diff_dict.items():
        actual_value, expected_value = values
        writer.writerow({
            'Metadata Tool': tool_name,
            'Metadata Field': key,
            'Expected Value': expected_value,
            'Actual Value': actual_value
        })

def parse_arguments():
    version_string = importlib.metadata.version('AV_Spex')
    parser = argparse.ArgumentParser(
        description=f"""\
%(prog)s {version_string}

AV Spex is a python application designed to help process digital audio and video media created from analog sources.
The scripts will confirm that the digital files conform to predetermined specifications.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {version_string}')
    parser.add_argument("paths", nargs='*', help="Path to the input -f: video file(s) or -d: directory(ies)")
    parser.add_argument("-dr","--dryrun", action="store_true", help="Flag to run av-spex w/out outputs or checks. Use to change config profiles w/out processing video.")
    parser.add_argument("--profile", choices=["step1", "step2"], help="Select processing profile (step1 or step2)")
    parser.add_argument("-sn","--signalflow", choices=["JPC_AV_SVHS"], help="Select signal flow config type (JPC_AV_SVHS)")
    parser.add_argument("-fn","--filename", choices=["jpc", "bowser"], help="Select file name config type (jpc or bowser)")
    parser.add_argument("-sp","--saveprofile", choices=["config", "command"], help="Flag to write current config.yaml or command_config.yaml settings to new a yaml file, for re-use or reference. Select config or command: --saveprofile command")
    parser.add_argument("-d", "--directory", action="store_true", help="Flag to indicate input is a directory")
    parser.add_argument("-f", "--file", action="store_true", help="Flag to indicate input is a video file")

    args = parser.parse_args()

    # Validate arguments
    if not args.dryrun and not args.paths:
        parser.error("the following arguments are required: paths")

    if args.dryrun:
        input_paths = []
    else:
        input_paths = args.paths
    source_directories = []

    for input_path in input_paths:
        if args.file:
            if not os.path.isfile(input_path):
                logger.critical(f"Error: {input_path} is not a valid file.")
                sys.exit(1)
            source_directories.append(os.path.dirname(input_path))
            logger.info(f'\nInput directory found: {(os.path.dirname(input_path))}\n')
        else:
            if not os.path.isdir(input_path):
                logger.critical(f"Error: {input_path} is not a valid directory.")
                sys.exit(1)
            source_directories.append(input_path)
            logger.info(f'\nInput directory found: {input_path}\n')

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

    dry_run_only = args.dryrun

    save_config_type = None
    user_profile_config = None
    if args.saveprofile:
        if args.saveprofile == 'config':
            save_config_type = config_path 
            config_dir = config_path.config_dir
            user_profile_config = os.path.join(config_dir, f"config_profile_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.yaml")
        elif args.saveprofile == 'command':
            save_config_type = command_config
            config_dir = command_config.config_dir
            user_profile_config = os.path.join(config_dir, f"command_profile_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.yaml")

    return source_directories, selected_profile, sn_config_changes, fn_config_changes, dry_run_only, save_config_type, user_profile_config

def main():
    '''
    av-spex takes 1 input file or directory as an argument, like this:
    av-spex <input_directory> (or -f <input_file.mkv>)
    it confirms the file is valid, generates metadata on the file, then checks it against expected values.
    '''

    avspex_icon = text2art("A-V Spex",font='5lineoblique')
    print(f'\n{avspex_icon}\n\n')
    time.sleep(1)
    
    source_directories, selected_profile, sn_config_changes, fn_config_changes, dry_run_only, save_config_type, user_profile_config = parse_arguments()

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

    if save_config_type:
        save_profile_to_file(save_config_type, user_profile_config)

    if dry_run_only:
        logger.critical(f"Dry run selected. Exiting now.\n\n")
        sys.exit(1)

    # Reload the dictionaries if the profile has been applied
    config_path.reload()
    command_config.reload()
    
    check_filenames(source_directories)

    overall_start_time = time.time()
    
    for source_directory in source_directories:
        dir_start_time = time.time()

        source_directory = os.path.normpath(source_directory)
        # sanitize user input directory path
        
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
            if existing_tags:
                existing_video_hash, existing_audio_hash = extract_hashes(existing_tags)
            else:
                existing_video_hash = None 
                existing_audio_hash = None
            # Check if VIDEO_STREAM_HASH and AUDIO_STREAM_HASH MKV tags exists
            if existing_video_hash is None or existing_audio_hash is None :
                embed_fixity(video_path)
            else:
                logger.critical(f"Existing stream hashes found!")
                if command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'yes':
                    logger.critical(f'New stream hashes will be generated and old hashes will be overwritten!')
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
        
        # Run mediaconch on the video file and save the output to a csv file
        mediaconch_output_path = None
        # need to initialize path for report
        if command_config.command_dict['tools']['mediaconch']['run_mediaconch'] == 'yes':
            mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
            run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

            # open the mediaconch csv output and check for the word 'fail'
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

        # Initiate dictionaries for storing differences between actual values and expected values
        exiftool_differences = None
        mediainfo_differences = None
        mediatrace_differences = None
        ffprobe_differences = None
        
        # Run exiftool, mediainfo and ffprobe using the 'run_command' function
        exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
        if command_config.command_dict['tools']['exiftool']['run_exiftool'] == 'yes':
            run_command('exiftool', video_path, '>', exiftool_output_path)

        if command_config.command_dict['tools']['exiftool']['check_exiftool'] == 'yes':
            # If check_exfitool is set to 'yes' in command_config.yaml then
            exiftool_differences = parse_exiftool(exiftool_output_path)
            # Run parse functions defined in the '_check.py' scripts

        if not os.path.isfile(exiftool_output_path):
            exiftool_output_path = None
            # reset variable if no output is created, so that it won't print in the report

        mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
        if command_config.command_dict['tools']['mediainfo']['run_mediainfo'] == 'yes':
            run_command('mediainfo -f', video_path, '>', mediainfo_output_path)
        
        if command_config.command_dict['tools']['mediainfo']['check_mediainfo'] == 'yes':
            # If check_mediainfo is set to 'yes' in command_config.yaml then
            mediainfo_differences = parse_mediainfo(mediainfo_output_path)
            # Run parse functions defined in the '_check.py' scripts

        if not os.path.isfile(mediainfo_output_path):
            mediainfo_output_path = None
            # reset variable if no output is created, so that it won't print in the report
            
        mediatrace_output_path = os.path.join(destination_directory, f'{video_id}_mediatrace_output.xml')
        if command_config.command_dict['tools']['mediainfo']['check_mediainfo'] == 'yes':
            logger.info(f"\nCreating MediaTrace XML file to check custom MKV Tag metadata fields:")
            # If check_mediainfo is set to 'yes' in command_config.yaml then
            run_command("mediainfo --Details=1 --Output=XML", video_path, '>', mediatrace_output_path)
            mediatrace_differences = parse_mediatrace(mediatrace_output_path)
            # Run parse functions defined in the '_check.py' scripts

        ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
        if command_config.command_dict['tools']['ffprobe']['run_ffprobe'] == 'yes':
            run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, '>', ffprobe_output_path)

        if command_config.command_dict['tools']['ffprobe']['check_ffprobe'] == 'yes':
            # If check_ffprobe is set to 'yes' in command_config.yaml then
            ffprobe_differences = parse_ffprobe(ffprobe_output_path)
            # Run parse functions defined in the '_check.py' scripts

        if not os.path.isfile(ffprobe_output_path):
            ffprobe_output_path = None
            # reset variable if no output is created, so that it won't print in the report
        
        # Create 'report directory' for csv files in html report
        report_directory = make_report_dir(source_directory, video_id) 
        diff_csv_path = None
        # need to initialize path for report
        if command_config.command_dict['outputs']['report'] == 'yes':
            if exiftool_differences and mediainfo_differences and ffprobe_differences and mediatrace_differences is None:
                logger.info(f"All specified metadata fields and values found, no CSV report written")
            else:
                # Create CSV for storing differences between expected metadata values and actual values
                csv_name = video_id + '_' + 'metadata_difference'
                diff_csv_path = os.path.join(report_directory, f'{csv_name}.csv')
                if os.path.exists(diff_csv_path):
                    # if CSV file already exists, append a timestamp to the new csv_name
                    timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
                    csv_name += '_' + timestamp
                    diff_csv_path = os.path.join(report_directory, f'{csv_name}.csv')

                # Open CSV file in write mode
                with open(diff_csv_path, 'w', newline='') as diffs_csv:
                    # Define CSV header
                    fieldnames = ['Metadata Tool', 'Metadata Field', 'Expected Value', 'Actual Value']
                    writer = csv.DictWriter(diffs_csv, fieldnames=fieldnames)
                    # Write header to CSV file
                    writer.writeheader()
                    if exiftool_differences:
                        write_to_csv(exiftool_differences, 'exiftool', writer)
                    if mediainfo_differences:
                        write_to_csv(mediainfo_differences, 'mediainfo', writer)
                    if mediatrace_differences:
                        write_to_csv(mediatrace_differences, 'mediatrace', writer)  
                    if ffprobe_differences:
                        write_to_csv(ffprobe_differences, 'ffprobe', writer)

        qctools_ext = command_config.command_dict['outputs']['qctools_ext']
        qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
        if command_config.command_dict['tools']['qctools']['run_qctools'] == 'yes':
            run_command('qcli -i', video_path, '-o', qctools_output_path)

        if command_config.command_dict['tools']['qctools']['check_qctools'] == 'yes':
            if not os.path.isfile(qctools_output_path):
                logger.critical(f"\nUnable to check qctools report. No file found at this path: {qctools_output_path}.\n")
                qctools_check_output = None
            else:
                run_qctparse(video_path, qctools_output_path, report_directory)
        else:
            qctools_check_output = None
        
        access_output_path = os.path.join(source_directory, f'{video_id}_access.mp4')
        if command_config.command_dict['outputs']['access_file'] == 'yes':
            if os.path.isfile(access_output_path):
                logger.critical(f"Access file already exists, not running ffmpeg")
            else:
                make_access_file(video_path, access_output_path)
        
        if command_config.command_dict['outputs']['report'] == 'yes':
            html_report_path = os.path.join(source_directory, f'{video_id}_avspex_report.html')
            write_html_report(video_id,report_directory,html_report_path)
            
        logger.debug(f'\n\nPlease note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!')
        
        ascii_video_id = text2art(video_id, font='small')

        logger.warning(f'\nProcessing complete:\n{ascii_video_id}')
        logger.info(f'\nOutput files saved in the directory: {destination_directory}')

        dir_end_time = time.time()
        dir_total_time = dir_end_time - dir_start_time
        formatted_total_time = time.strftime("%H:%M:%S", time.gmtime(dir_total_time))

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
