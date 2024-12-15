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

from PyQt6.QtWidgets import (
    QApplication
)

from .processing import processing_mgmt
from .processing import run_tools
from .utils import yaml_profiles
from .utils import dir_setup
from .utils import edit_config
from .utils.log_setup import logger
from .utils.deps_setup import required_commands, check_external_dependency, check_py_version
from .utils.find_config import config_path, command_config, yaml
from .utils.gui_setup import ConfigWindow, MainWindow



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
    gui: Optional[Any]


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
    parser.add_argument('--gui', action='store_true', 
                        help='Force launch in GUI mode')
    

    # Parse arguments
    args = parser.parse_args()

    # Validate and process arguments
    if not args.dryrun and not args.paths and not args.gui:
        parser.error("the following arguments are required: paths")

    input_paths = [] if args.dryrun else args.paths
    source_directories = dir_setup.validate_input_paths(input_paths, args.file)

    # Determine save_config_type based on saveprofile
    if args.saveprofile == 'config':
        save_config_type = config_path
    elif args.saveprofile == 'command':
        save_config_type = command_config
    else:
        save_config_type = None

    # Resolve configurations using mapping functions
    selected_profile = edit_config.resolve_config(args.profile, PROFILE_MAPPING)
    sn_config_changes = edit_config.resolve_config(args.signalflow, SIGNALFLOW_MAPPING)
    fn_config_changes = edit_config.resolve_config(args.filename, FILENAME_MAPPING)

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
        tools_off_names=args.off or [],
        gui=args.gui
    )


def _generate_profile_filename(saveprofile):
    if not saveprofile:
        return None
    config_dir = (config_path.config_dir if saveprofile == 'config' 
                  else command_config.config_dir)
    profile_type = 'config' if saveprofile == 'config' else 'command'
    return os.path.join(config_dir, 
                        f"{profile_type}_profile_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.yaml")


def create_processing_timer():
    """
    Create a context manager for tracking processing time.
    
    Returns:
        ProcessingTimer: A context manager for timing operations
    """
    
    class ProcessingTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.total_time = 0  # Initialize to 0 to avoid NoneType issues

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()
            self.total_time = self.end_time - self.start_time

        def get_formatted_time(self):
            """
            Get formatted time string for total processing duration.
            
            Returns:
                str: Formatted time (HH:MM:SS)
            """
            # Ensure total_time is valid
            if self.total_time is None:
                return "00:00:00"
            
            hours, remainder = divmod(int(self.total_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        def log_time_details(self, video_id):
            """
            Log detailed time information.
            
            Args:
                video_id (str): Identifier for the processed video
            """
            if self.start_time is None or self.end_time is None:
                logger.error("Timer was not properly started or stopped.")
                return
            
            logger.info(
                f'Process time for {video_id}: '
                f'time start: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time))}; '
                f'time end: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time))}; '
                f'total time: {self.get_formatted_time()}'
            )

    return ProcessingTimer()


def display_processing_banner(video_id=None):
    """
    Display ASCII art banners before and after processing.
    
    Args:
        video_id (str, optional): Video identifier for additional banner
    """
    tape_icon = art('cassette1')
    banner = f'\n{tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}    {tape_icon}\n'
    print(banner)

    if video_id:
        ascii_video_id = text2art(video_id, font='tarty2')
        logger.warning(f'Processing complete:{ascii_video_id}\n')


def process_directories(source_directories):
    for source_directory in source_directories:
        # sanitize user input directory path
        source_directory = os.path.normpath(source_directory)
        process_single_directory(source_directory)


def process_single_directory(source_directory):

    # Display initial processing banner
    display_processing_banner()

    # Use processing timer for tracking
    with create_processing_timer() as timer:
        try:
            # Call the new prep_directory function
            init_dir_result = dir_setup.initialize_directory(source_directory)
            if init_dir_result is None:
                return  # Skip to the next source_directory if preparation failed

            # Unpack the returned values
            video_path, video_id, destination_directory, access_file_found = init_dir_result

            processing_mgmt.process_fixity(source_directory, video_path, video_id)

            mediaconch_results = processing_mgmt.validate_video_with_mediaconch(
            video_path, 
            destination_directory, 
            video_id, 
            command_config, 
            config_path
            )

            metadata_differences = processing_mgmt.process_video_metadata(
                video_path, 
                destination_directory, 
                video_id, 
                command_config
                )

            processing_results = processing_mgmt.process_video_outputs(
                video_path,
                source_directory,
                destination_directory,
                video_id,
                command_config,
                metadata_differences
            )

            logger.debug(f'Please note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!\n')

            # Display final processing banner
            display_processing_banner(video_id)

        except Exception as e:
            logger.critical(f"Error processing directory {source_directory}: {e}")
            return None
        finally:
            # Optional brief pause between directory processing
            time.sleep(1)

    # Log processing time
    timer.log_time_details(video_id)


def print_av_spex_logo():
    avspex_icon = text2art("A-V Spex", font='5lineoblique')
    print(f'{avspex_icon}\n')


def print_nmaahc_logo():
    nmaahc_icon = text2art("nmaahc",font='tarty1')
    print(f'{nmaahc_icon}\n')


def log_overall_time(overall_start_time, overall_end_time):
    logger.warning(f'All files processed!\n')
    overall_total_time = overall_end_time - overall_start_time
    formatted_overall_time = time.strftime("%H:%M:%S", time.gmtime(overall_total_time))
    logger.info(f"Overall processing time for all directories: {formatted_overall_time}\n")

    return formatted_overall_time


def run_cli_mode(args):
    print_av_spex_logo()

    # Update YAML configs
    edit_config.update_yaml_configs(args.selected_profile, args.tool_names, args.tools_on_names, args.tools_off_names,
                        args.sn_config_changes, args.fn_config_changes, args.save_config_type,
                        args.user_profile_config)

    # Print config
    edit_config.print_config(args.print_config_profile)

    if args.dry_run_only:
        logger.critical("Dry run selected. Exiting now.")
        sys.exit(1)


def run_avspex(source_directories):
    '''
    av-spex takes 1 input file or directory as an argument, like this:
    av-spex <input_directory> (or -f <input_file.mkv>)
    it confirms the file is valid, generates metadata on the file, then checks it against expected values.
    '''

    check_py_version()

    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)

    # Reload the dictionaries if the profile has been applied
    config_path.reload()
    command_config.reload()

    overall_start_time = time.time()

    process_directories(source_directories)

    print_nmaahc_logo()

    overall_end_time = time.time()

    formatted_overall_time = log_overall_time(overall_start_time, overall_end_time)

def main_gui():
    app = QApplication(sys.argv)
    window = MainWindow(command_config, command_config.command_dict, config_path)
    window.show()
    app.exec()
    source_directories = window.get_source_directories()

    if source_directories:
        run_avspex(source_directories)


def main_cli():
    args = parse_arguments()

    if args.gui:
       main_gui()
    else:
        run_cli_mode(args)
        run_avspex(args.source_directories)


def main():
    # Default behavior based on command-line arguments
    args = parse_arguments()

    if args.gui or (args.source_directories is None and not sys.argv[1:]):
        main_gui()
    else:
        main_cli()


if __name__ == "__main__":
    main()

