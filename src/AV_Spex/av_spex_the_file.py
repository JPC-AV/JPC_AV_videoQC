#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import logging
import csv
import shutil
import argparse
import importlib.metadata
import time
import toml
from art import art, text2art
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Any

from .utils.log_setup import logger
from .utils.deps_setup import required_commands, check_external_dependency, check_py_version
from .utils.find_config import config_path, command_config, yaml
from .utils import yaml_profiles
from .utils.generate_report import write_html_report
from .checks.fixity_check import check_fixity, output_fixity
from .checks.filename_check import is_valid_filename
from .checks.mediainfo_check import parse_mediainfo
from .checks.mediatrace_check import parse_mediatrace
from .checks.exiftool_check import parse_exiftool
from .checks.ffprobe_check import parse_ffprobe
from .checks.embed_fixity import extract_tags, extract_hashes, embed_fixity, validate_embedded_md5
from .checks.make_access import make_access_file
from .checks.qct_parse import run_qctparse


@dataclass
class ParsedArguments:
    source_directories: List[str]
    selected_profile: Optional[Any]
    tool_names: List[str]
    sn_config_changes: Optional[Any]
    fn_config_changes: Optional[Any]
    print_config_profile: bool
    dry_run_only: bool
    save_config_type: Optional[Any]
    user_profile_config: Optional[str]
    tools_on_names: List[str]
    tools_off_names: List[str]


AVAILABLE_TOOLS = ["exiftool", "ffprobe", "mediaconch", "mediainfo", "mediatrace", "qctools"]


PROFILE_MAPPING = {
    "step1": yaml_profiles.profile_step1,
    "step2": yaml_profiles.profile_step2,
    "off": yaml_profiles.profile_allOff
}


SIGNALFLOW_MAPPING = {
    "JPC_AV_SVHS": yaml_profiles.JPC_AV_SVHS,
    "BVH3100": yaml_profiles.BVH3100
}


FILENAME_MAPPING = {
    "jpc": yaml_profiles.JPCAV_filename,
    "bowser": yaml_profiles.bowser_filename
}


def check_directory(source_directory, video_id):
    directory_name = os.path.basename(source_directory)
    # Check if the directory name starts with the base_video_id string
    if directory_name.startswith(video_id):
        logger.info(f'Directory name "{directory_name}" correctly matches video file name "{video_id}".\n')
    else:
        logger.critical(f'Directory name "{directory_name}" does not correctly match the expected "{video_id}".\n')    


def make_qc_output_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    destination_directory = os.path.join(source_directory, f'{video_id}_qc_metadata')

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    logger.debug(f'Metadata files will be written to {destination_directory}\n')

    return destination_directory


def make_report_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    report_directory = os.path.join(source_directory, f'{video_id}_report_csvs')

    if os.path.exists(report_directory):
        shutil.rmtree(report_directory)
    os.makedirs(report_directory)

    logger.debug(f'Report files will be written to {report_directory}\n')

    return report_directory


def run_command(command, input_path, output_type, output_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    # Get the current PATH environment variable
    env = os.environ.copy()
    env['PATH'] = '/usr/local/bin:' + env.get('PATH', '')

    full_command = f"{command} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'Running command: {full_command}\n')
    subprocess.run(full_command, shell=True, env=env)


def run_mediatrace_command(command, input_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    # Get the current PATH environment variable
    env = os.environ.copy()
    env['PATH'] = '/usr/local/bin:' + env.get('PATH', '')

    full_command = f"{command} \"{input_path}\" "

    logger.debug(f'Running mediainfo to generate MediaTrace XML: {full_command}')
    output = subprocess.run(full_command, shell=True, capture_output=True)

    return output


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
            logger.debug(f"Existing vrecord files found in {os.path.basename(directory)}/{os.path.basename(vrecord_directory)}\n")
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
            # logger.debug(f'Moved vrecord file: {filename} to directory: {os.path.basename(vrecord_directory)}')
            vrecord_files_found = True

    # Check if any matching files were found to create the directory
    if vrecord_files_found:
        logger.debug(f"Files generated by vrecord found. '{video_id}_vrecord_metadata' directory created and files moved.")
    else:
        logger.debug("No vrecord files found.\n")


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
            logger.info(f'Input video file found in {source_directory}: {video_path}\n')
        else:
            logger.critical(f'More than 1 mkv found in {source_directory}: {found_mkvs}\n')
            return None
    else:
        logger.critical(f"Error: No mkv video file found in the directory: {source_directory}\n")
        return None

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


def format_config_value(value, indent=0, is_nested=False):
    """
    Recursively formats dictionaries and lists for better presentation.
    """
    spacer = " " * indent
    formatted_str = ""

    if isinstance(value, dict):
        # Only add a newline before nested dictionaries, not for top-level keys
        if is_nested:
            formatted_str += "\n"
        for nested_key, nested_value in value.items():
            formatted_str += f"{spacer}{nested_key}: {format_config_value(nested_value, indent + 2, is_nested=True)}\n"
        return formatted_str
    elif isinstance(value, list):
        # Join list elements with commas, no brackets
        formatted_str = f"{', '.join(str(item) for item in value)}"
        return formatted_str
    elif value == 'yes':
        return "✅"  # Inline formatting for 'yes'
    elif value == 'no':
        return "❌"  # Inline formatting for 'no'
    else:
        # Handle non-dictionary, non-list values directly
        return f"{value}"
    
    
def update_yaml_configs(selected_profile, tool_names, tools_on_names, tools_off_names, 
                        sn_config_changes, fn_config_changes, save_config_type, 
                        user_profile_config):
    """Updates YAML configuration files based on provided parameters."""
    if selected_profile:
        yaml_profiles.apply_profile(command_config, selected_profile)
        logger.info(f'command_config.yaml updated to match selected tool profile\n')

    if tool_names:
        yaml_profiles.apply_by_name(command_config, tool_names)

    if tools_on_names:
        yaml_profiles.toggle_on(command_config, tools_on_names)

    if tools_off_names:
        yaml_profiles.toggle_off(command_config, tools_off_names)

    if sn_config_changes:
        yaml_profiles.update_config(config_path, 'ffmpeg_values.format.tags.ENCODER_SETTINGS', sn_config_changes)
        yaml_profiles.update_config(config_path, 'mediatrace.ENCODER_SETTINGS', sn_config_changes)

    if fn_config_changes:
        yaml_profiles.update_config(config_path, 'filename_values', fn_config_changes)

    if save_config_type:
        yaml_profiles.save_profile_to_file(save_config_type, user_profile_config)


def print_config(print_config_profile):
    """Prints the current configuration if requested."""
    if print_config_profile:
        logger.debug("The current config profile settings are:\n")
        command_config.reload()
        for key, value in command_config.command_dict.items():
            logging.warning(f"{key}:")
            logging.info(f"{format_config_value(value, indent=2)}")


def validate_input_paths(input_paths, is_file_mode):
    source_directories = []
    for input_path in input_paths:
        try:
            if is_file_mode and not os.path.isfile(input_path):
                raise ValueError(f"Error: {input_path} is not a valid file.")
            elif not is_file_mode and not os.path.isdir(input_path):
                raise ValueError(f"Error: {input_path} is not a valid directory.")
            
            directory = os.path.dirname(input_path) if is_file_mode else input_path
            source_directories.append(directory)
            logger.info(f'Input directory found: {directory}\n')
        except ValueError as e:
            logger.critical(str(e))
            sys.exit(1)
    return source_directories


def resolve_config(args, config_mapping):
    return config_mapping.get(args, None)


def parse_arguments():
    # Read version from pyproject.toml
    pyproject_path = os.path.join(os.path.dirname(config_path.config_dir), 'pyproject.toml')
    with open(pyproject_path, 'r') as f:
        version_string = toml.load(f)['project']['version']

    # Create argument parser
    parser = argparse.ArgumentParser(
        description=f"""\
%(prog)s {version_string}

AV Spex is a python application designed to help process digital audio and video media created from analog sources.
The scripts will confirm that the digital files conform to predetermined specifications.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add arguments (with AVAILABLE_TOOLS as choices)
    parser.add_argument('--version', action='version', version=f'%(prog)s {version_string}')
    parser.add_argument("paths", nargs='*', help="Path to the input -f: video file(s) or -d: directory(ies)")
    parser.add_argument("-dr","--dryrun", action="store_true", 
                        help="Flag to run av-spex w/out outputs or checks. Use to change config profiles w/out processing video.")
    parser.add_argument("--profile", choices=list(PROFILE_MAPPING.keys()), 
                        help="Select processing profile or turn checks off")
    parser.add_argument("-t", "--tool", choices=AVAILABLE_TOOLS, 
                        action='append', help="Select individual tools to enable")
    parser.add_argument("--on", choices=AVAILABLE_TOOLS, 
                        action='append', help="Select specific tools to turn on")
    parser.add_argument("--off", choices=AVAILABLE_TOOLS, 
                        action='append', help="Select specific tools to turn off")
    parser.add_argument("-sn","--signalflow", choices=SIGNALFLOW_MAPPING,
                        help="Select signal flow config type (JPC_AV_SVHS or BVH3100")
    parser.add_argument("-fn","--filename", choices=FILENAME_MAPPING, 
                        help="Select file name config type (jpc or bowser)")
    parser.add_argument("-sp","--saveprofile", choices=["config", "command"], 
                        help="Flag to write current config.yaml or command_config.yaml settings to new a yaml file, for re-use or reference.")
    parser.add_argument("-pp","--printprofile", action="store_true", 
                        help="Show current config profile.")
    parser.add_argument("-d","--directory", action="store_true", 
                        help="Flag to indicate input is a directory")
    parser.add_argument("-f","--file", action="store_true", 
                        help="Flag to indicate input is a video file")
    

    # Parse arguments
    args = parser.parse_args()

    # Validate and process arguments
    if not args.dryrun and not args.paths:
        parser.error("the following arguments are required: paths")

    input_paths = [] if args.dryrun else args.paths
    source_directories = validate_input_paths(input_paths, args.file)

    # Determine save_config_type based on saveprofile
    if args.saveprofile == 'config':
        save_config_type = config_path
    elif args.saveprofile == 'command':
        save_config_type = command_config
    else:
        save_config_type = None

    # Resolve configurations using mapping functions
    selected_profile = resolve_config(args.profile, PROFILE_MAPPING)
    sn_config_changes = resolve_config(args.signalflow, SIGNALFLOW_MAPPING)
    fn_config_changes = resolve_config(args.filename, FILENAME_MAPPING)

    # Return parsed arguments
    return ParsedArguments(
        source_directories=source_directories,
        selected_profile=selected_profile,
        tool_names=args.tool or [],
        sn_config_changes=sn_config_changes,
        fn_config_changes=fn_config_changes,
        print_config_profile=args.printprofile,
        dry_run_only=args.dryrun,
        save_config_type=save_config_type,
        user_profile_config=_generate_profile_filename(args.saveprofile),
        tools_on_names=args.on or [],
        tools_off_names=args.off or []
    )


def _generate_profile_filename(saveprofile):
    if not saveprofile:
        return None
    config_dir = (config_path.config_dir if saveprofile == 'config' 
                  else command_config.config_dir)
    profile_type = 'config' if saveprofile == 'config' else 'command'
    return os.path.join(config_dir, 
                        f"{profile_type}_profile_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.yaml")


def process_directories(source_directories):
    for source_directory in source_directories:
        process_single_directory(source_directory)


def initialize_directory(source_directory):
    """
    Prepare the directory for processing by finding the video file 
    and validating the filename.

    Args:
        source_directory (str): Path to the source directory

    Returns:
        tuple: (video_path, video_id, destination_directory) if successful
        None if preparation fails
    """
    video_path = find_mkv(source_directory)

    if video_path is None:
        logger.warning(f"Skipping {source_directory} due to error.\n")
        return None  # Indicates preparation failed

    valid_filename = is_valid_filename(video_path)

    if valid_filename is False:
        logger.warning(f"Skipping {source_directory} due to error.\n")
        return None  # Indicates preparation failed

    logger.warning(f'Now processing {video_path}\n')

    # outputs video_id (i.e. 'JPC_AV_05000')
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    # Check to confirm directory is the same name as the video file name
    check_directory(source_directory, video_id)

    # Create 'destination directory' for qc outputs
    destination_directory = make_qc_output_dir(source_directory, video_id)

    # Moves vrecord files to subdirectory  
    move_vrec_files(source_directory, video_id)

    # Iterate through files in the directory to identify access file
    access_file_found = None
    for filename in os.listdir(source_directory):
        if filename.lower().endswith('mp4'):
            access_file_found = filename
            logger.info("Existing access file found!\n")
            break

    return video_path, video_id, destination_directory, access_file_found


def process_embedded_fixity(video_path):
    """
    Handles embedding stream fixity tags in the video file.
    """
    existing_tags = extract_tags(video_path)
    if existing_tags:
        existing_video_hash, existing_audio_hash = extract_hashes(existing_tags)
    else:
        existing_video_hash = None
        existing_audio_hash = None

    # Check if VIDEO_STREAM_HASH and AUDIO_STREAM_HASH MKV tags exist
    if existing_video_hash is None or existing_audio_hash is None:
        embed_fixity(video_path)
    else:
        logger.critical("Existing stream hashes found!")
        if command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'yes':
            logger.critical('New stream hashes will be generated and old hashes will be overwritten!')
            embed_fixity(video_path)
        elif command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'no':
            logger.error('Not writing stream hashes to MKV\n')
        elif command_config.command_dict['outputs']['fixity']['overwrite_stream_fixity'] == 'ask me':
            # User input for handling existing stream hashes
            while True:
                user_input = input("Do you want to overwrite existing stream hashes? (yes/no): ")
                if user_input.lower() in ["yes", "y"]:
                    embed_fixity(video_path)
                    break
                elif user_input.lower() in ["no", "n"]:
                    logger.debug('Not writing stream hashes to MKV')
                    break
                else:
                    print("Invalid input. Please enter yes/no.")


def process_fixity(source_directory, video_path, video_id):
    """
    Orchestrates the entire fixity process, including embedded and file-level operations.
    """
    # Embed stream fixity if required
    if command_config.command_dict['outputs']['fixity']['embed_stream_fixity'] == 'yes':
        process_embedded_fixity(video_path)

    # Validate stream hashes if required
    if command_config.command_dict['outputs']['fixity']['check_stream_fixity'] == 'yes':
        validate_embedded_md5(video_path)

    # Initialize md5_checksum variable, so it is 'None' if not assigned in output_fixity
    md5_checksum = None
    # Create checksum for video file and output results
    if command_config.command_dict['outputs']['fixity']['output_fixity'] == 'yes':
        md5_checksum = output_fixity(source_directory, video_path)

    # Verify stored checksum and write results
    if command_config.command_dict['outputs']['fixity']['check_fixity'] == 'yes':
        check_fixity(source_directory, video_id, actual_checksum=md5_checksum)


def run_tool_command(tool_name, video_path, destination_directory, video_id, command_config):
    """
    Run a specific metadata extraction tool and generate its output file.
    
    Args:
        tool_name (str): Name of the tool to run (e.g., 'exiftool', 'mediainfo')
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        command_config (object): Configuration object with tool settings
        
    Returns:
        str or None: Path to the output file, or None if tool is not run
    """
    # Define tool-specific command configurations
    tool_commands = {
        'exiftool': {
            'command': 'exiftool',
            'config_key': 'run_exiftool'
        },
        'mediainfo': {
            'command': 'mediainfo -f',
            'config_key': 'run_mediainfo'
        },
        'mediatrace': {
            'command': 'mediainfo --Details=1 --Output=XML',
            'config_key': 'run_mediatrace'
        },
        'ffprobe': {
            'command': 'ffprobe -v error -hide_banner -show_format -show_streams -print_format json',
            'config_key': 'run_ffprobe'
        }
    }

    # Check if the tool is configured to run
    tool_config = tool_commands.get(tool_name)
    if not tool_config:
        logger.error(f"tool command is not configured correctly: {tool_name}")
        return None

    # Construct output path
    output_path = os.path.join(destination_directory, f'{video_id}_{tool_name}_output.{_get_file_extension(tool_name)}')
    
    # Check if tool should be run based on configuration
    if command_config.command_dict['tools'][tool_name][tool_config['config_key']] == 'yes':
        if tool_name == 'mediatrace':
            logger.debug(f"Creating {tool_name.capitalize()} XML file to check custom MKV Tag metadata fields:")
        
        # Run the tool command
        run_command(tool_config['command'], video_path, '>', output_path)
        
        return output_path if os.path.isfile(output_path) else None
    
    return None

def _get_file_extension(tool_name):
    """
    Get the appropriate file extension for each tool's output.
    
    Args:
        tool_name (str): Name of the tool
        
    Returns:
        str: File extension for the tool's output
    """
    extension_map = {
        'exiftool': 'txt',
        'mediainfo': 'txt',
        'mediatrace': 'xml',
        'ffprobe': 'txt'
    }
    return extension_map.get(tool_name, 'txt')

def check_tool_metadata(tool_name, output_path, command_config):
    """
    Check metadata for a specific tool if configured.
    
    Args:
        tool_name (str): Name of the tool
        output_path (str): Path to the tool's output file
        command_config (object): Configuration object with tool settings
        
    Returns:
        dict or None: Differences found by parsing the tool's output, or None
    """
    # Mapping of tool names to their parsing functions
    parse_functions = {
        'exiftool': parse_exiftool,
        'mediainfo': parse_mediainfo,
        'mediatrace': parse_mediatrace,
        'ffprobe': parse_ffprobe
    }

    # Check if tool metadata checking is enabled
    if output_path and command_config.command_dict['tools'][tool_name][f'check_{tool_name}'] == 'yes':
        parse_function = parse_functions.get(tool_name)
        if parse_function:
            return parse_function(output_path)
    
    return None

def process_video_metadata(video_path, destination_directory, video_id, command_config):
    """
    Main function to process video metadata using multiple tools.
    
    Args:
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        command_config (object): Configuration object with tool settings
        
    Returns:
        dict: Dictionary of metadata differences from various tools
    """
    # List of tools to process
    tools = ['exiftool', 'mediainfo', 'mediatrace', 'ffprobe']
    
    # Store differences for each tool
    metadata_differences = {}
    
    # Process each tool
    for tool in tools:
        # Run tool and get output path
        output_path = run_tool_command(tool, video_path, destination_directory, video_id, command_config)
        
        # Check metadata and store differences
        differences = check_tool_metadata(tool, output_path, command_config)
        if differences:
            metadata_differences[tool] = differences
    
    return metadata_differences


def find_mediaconch_policy(command_config, config_path):
    """
    Find and validate the MediaConch policy file.
    
    Args:
        command_config (object): Configuration object with tool settings
        config_path (object): Configuration path object
        
    Returns:
        str or None: Full path to the policy file, or None if not found
    """
    try:
        # Get policy filename from configuration
        policy_file = command_config.command_dict['tools']['mediaconch']['mediaconch_policy']
        policy_path = os.path.join(config_path.config_dir, policy_file)

        if not os.path.exists(policy_path):
            logger.critical(f'Policy file not found: {policy_file}')
            return None

        logger.debug(f'Using MediaConch policy {policy_file}')
        return policy_path

    except KeyError as e:
        logger.critical(f'Configuration error: {e}')
        return None
    except Exception as e:
        logger.critical(f'Unexpected error finding MediaConch policy: {e}')
        return None


def run_mediaconch_command(command, input_path, output_type, output_path, policy_path):
    """
    Run MediaConch command with specified policy and input file.
    
    Args:
        command (str): Base MediaConch command
        input_path (str): Path to the input video file
        output_type (str): Output type flag (e.g., -oc for CSV)
        output_path (str): Path to save the output file
        policy_path (str): Path to the MediaConch policy file
        
    Returns:
        bool: True if command executed successfully, False otherwise
    """
    try:
        # Construct full command
        full_command = f"{command} {policy_path} \"{input_path}\" {output_type} {output_path}"
        
        logger.debug(f'Running command: {full_command}\n')
        
        # Run the command
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        
        # Check for command execution errors
        if result.returncode != 0:
            logger.error(f"MediaConch command failed: {result.stderr}")
            return False
        
        return True

    except Exception as e:
        logger.critical(f'Error running MediaConch command: {e}')
        return False


def parse_mediaconch_output(output_path):
    """
    Parse MediaConch CSV output and log policy validation results.
    
    Args:
        output_path (str): Path to the MediaConch CSV output file
        
    Returns:
        dict: Validation results with pass/fail status for each policy check
    """
    try:
        with open(output_path, 'r', newline='') as mc_file:
            reader = csv.reader(mc_file)
            mc_header = next(reader)  # Get the header row
            mc_values = next(reader)  # Get the values row

            # Create a dictionary to track validation results
            validation_results = {}
            found_failures = False

            # Zip headers and values to create key-value pairs
            for mc_field, mc_value in zip(mc_header, mc_values):
                validation_results[mc_field] = mc_value

                # Check for failures
                if mc_value == "fail":
                    if not found_failures:
                        logger.critical("MediaConch policy failed:")
                        found_failures = True
                    logger.critical(f"{mc_field}: {mc_value}")

            # Log overall validation status
            if not found_failures:
                logger.info("MediaConch policy passed")
            else:
                logger.debug("")  # Add empty line after mediaconch results

            return validation_results

    except FileNotFoundError:
        logger.critical(f"MediaConch output file not found: {output_path}")
        return {}
    except csv.Error as e:
        logger.critical(f"Error parsing MediaConch CSV: {e}")
        return {}
    except Exception as e:
        logger.critical(f"Unexpected error processing MediaConch output: {e}")
        return {}

def validate_video_with_mediaconch(video_path, destination_directory, video_id, command_config, config_path):
    """
    Coordinate the entire MediaConch validation process.
    
    Args:
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        command_config (object): Configuration object with tool settings
        config_path (object): Configuration path object
        
    Returns:
        dict: Validation results from MediaConch policy check
    """
    # Check if MediaConch should be run
    if command_config.command_dict['tools']['mediaconch']['run_mediaconch'] != 'yes':
        logger.info("MediaConch validation skipped")
        return {}

    # Find the policy file
    policy_path = find_mediaconch_policy(command_config, config_path)
    if not policy_path:
        return {}

    # Prepare output path
    mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')

    # Run MediaConch command
    if not run_mediaconch_command(
        'mediaconch -p', 
        video_path, 
        '-oc', 
        mediaconch_output_path, 
        policy_path
    ):
        return {}

    # Parse and validate MediaConch output
    validation_results = parse_mediaconch_output(mediaconch_output_path)

    return validation_results


def process_single_directory(source_directory):
    dir_start_time = time.time()

    tape_icon = art('cassette1')

    print(f'\n{tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}\n')

    source_directory = os.path.normpath(source_directory)
    # sanitize user input directory path

    # Call the new prep_directory function
    init_dir_result = initialize_directory(source_directory)
    if init_dir_result is None:
        return  # Skip to the next source_directory if preparation failed

    # Unpack the returned values
    video_path, video_id, destination_directory, access_file_found = init_dir_result

    process_fixity(source_directory, video_path, video_id)

    mediaconch_results = validate_video_with_mediaconch(
     video_path, 
     destination_directory, 
     video_id, 
     command_config, 
     config_path
     )

    metadata_differences = process_video_metadata(
        video_path, 
        destination_directory, 
        video_id, 
        command_config
        )

    if command_config.command_dict['outputs']['report'] == 'yes':
        # Create 'report directory' for csv files in html report
        report_directory = make_report_dir(source_directory, video_id) 
        diff_csv_path = None
        # if any of the 'differences' lists are not None, then:
        if metadata_differences:
            # Create CSV for storing differences between expected metadata values and actual values
            csv_name = video_id + '_' + 'metadata_difference'
            diff_csv_path = os.path.join(report_directory, f'{csv_name}.csv')
            # Open CSV file in write mode
            with open(diff_csv_path, 'w', newline='') as diffs_csv:
                # Define CSV header
                fieldnames = ['Metadata Tool', 'Metadata Field', 'Expected Value', 'Actual Value']
                writer = csv.DictWriter(diffs_csv, fieldnames=fieldnames)
                # Write header to CSV file
                writer.writeheader()
                if metadata_differences['exiftool']:
                    write_to_csv(metadata_differences['exiftool'], 'exiftool', writer)
                if metadata_differences['mediainfo']:
                    write_to_csv(metadata_differences['mediainfo'], 'mediainfo', writer)
                if metadata_differences['mediatrace']:
                    write_to_csv(metadata_differences['mediatrace'], 'mediatrace', writer)  
                if metadata_differences['ffprobe']:
                    write_to_csv(metadata_differences['ffprobe'], 'ffprobe', writer)
        else:
            logger.info(f"All specified metadata fields and values found, no CSV report written\n")

    qctools_ext = command_config.command_dict['outputs']['qctools_ext']
    qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
    if command_config.command_dict['tools']['qctools']['run_qctools'] == 'yes':
        run_command('qcli -i', video_path, '-o', qctools_output_path)
        logger.debug('')  # adding a new line under qcli output for cleaner terminal output

    if command_config.command_dict['tools']['qctools']['check_qctools'] == 'yes':
        if not os.path.isfile(qctools_output_path):
            logger.critical(f"Unable to check qctools report. No file found at this path: {qctools_output_path}.\n")
            qctools_check_output = None
        else:
            if not report_directory:
                report_directory = make_report_dir(source_directory, video_id)
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
        write_html_report(video_id,report_directory,destination_directory,html_report_path)

    logger.debug(f'Please note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!\n')

    ascii_video_id = text2art(video_id, font='tarty2')

    logger.warning(f'Processing complete:{ascii_video_id}\n')
    logger.info(f'Output files saved in the directory: {destination_directory}\n')

    dir_end_time = time.time()
    dir_total_time = dir_end_time - dir_start_time
    formatted_total_time = time.strftime("%H:%M:%S", time.gmtime(dir_total_time))

    logger.info(f'Process time for {video_id}: time start: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dir_start_time))}; time end: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dir_end_time))}; total time: {formatted_total_time}')

    print(f'\n{tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}\n')

    time.sleep(1)


def main():
    '''
    av-spex takes 1 input file or directory as an argument, like this:
    av-spex <input_directory> (or -f <input_file.mkv>)
    it confirms the file is valid, generates metadata on the file, then checks it against expected values.
    '''

    avspex_icon = text2art("A-V Spex", font='5lineoblique')
    print(f'{avspex_icon}\n')

    args = parse_arguments()

    check_py_version()

    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)

    # Update YAML configs
    update_yaml_configs(args.selected_profile, args.tool_names, args.tools_on_names, args.tools_off_names,
                        args.sn_config_changes, args.fn_config_changes, args.save_config_type,
                        args.user_profile_config)

    # Print config
    print_config(args.print_config_profile)

    if args.dry_run_only:
        logger.critical("Dry run selected. Exiting now.")
        sys.exit(1)

    # Reload the dictionaries if the profile has been applied
    config_path.reload()
    command_config.reload()

    overall_start_time = time.time()

    process_directories(args.source_directories)

    nmaahc_icon = text2art("nmaahc",font='tarty1')
    print(f'{nmaahc_icon}\n')

    logger.warning(f'All files processed!\n')
    overall_end_time = time.time()
    overall_total_time = overall_end_time - overall_start_time
    formatted_overall_time = time.strftime("%H:%M:%S", time.gmtime(overall_total_time))
    logger.info(f"Overall processing time for all directories: {formatted_overall_time}\n")


if __name__ == "__main__":
    main()
