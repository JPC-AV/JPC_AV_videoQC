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
from .utils import dir_setup
from .utils import edit_config
from .utils.log_setup import logger
from .utils.deps_setup import required_commands, check_external_dependency, check_py_version
from .utils.setup_config import ChecksConfig, SpexConfig
from .utils.config_manager import ConfigManager
from .utils.config_io import ConfigIO
from .utils.gui_setup import ConfigWindow, MainWindow

config_mgr = ConfigManager()

@dataclass
class ParsedArguments:
    source_directories: List[str]
    selected_profile: Optional[Any]
    tool_names: List[str]
    sn_config_changes: Optional[Any]
    fn_config_changes: Optional[Any]
    print_config_profile: bool
    dry_run_only: bool
    tools_on_names: List[str]
    tools_off_names: List[str]
    gui: Optional[Any]
    export_config: Optional[str]
    export_file: Optional[str] 
    import_config: Optional[str]
    mediaconch_policy: Optional[str]


AVAILABLE_TOOLS = ["exiftool", "ffprobe", "mediaconch", "mediainfo", "mediatrace", "qctools"]


PROFILE_MAPPING = {
    "step1": edit_config.profile_step1,
    "step2": edit_config.profile_step2,
    "off": edit_config.profile_allOff
}


SIGNALFLOW_MAPPING = {
    "JPC_AV_SVHS": edit_config.JPC_AV_SVHS,
    "BVH3100": edit_config.BVH3100
}


FILENAME_MAPPING = {
    "jpc": edit_config.JPCAV_filename,
    "bowser": edit_config.bowser_filename
}


SIGNAL_FLOW_CONFIGS = {
    "JPC_AV_SVHS": {
        "format_tags": {"ENCODER_SETTINGS": edit_config.JPC_AV_SVHS},
        "mediatrace": {"ENCODER_SETTINGS": edit_config.JPC_AV_SVHS}
    },
    "BVH3100": {
        "format_tags": {"ENCODER_SETTINGS": edit_config.BVH3100}, 
        "mediatrace": {"ENCODER_SETTINGS": edit_config.BVH3100}
    }
}



def parse_arguments():
    project_path = os.path.dirname(os.path.dirname(config_mgr.project_root))
    pyproject_path = os.path.join(project_path, 'pyproject.toml')
    with open(pyproject_path, 'r') as f:
        version_string = toml.load(f)['project']['version']

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
    parser.add_argument("-dr","--dryrun", action="store_true", 
                        help="Flag to run av-spex w/out outputs or checks. Use to change config profiles w/out processing video.")
    parser.add_argument("--profile", choices=list(PROFILE_MAPPING.keys()), 
                        help="Select processing profile or turn checks off")
    parser.add_argument("-t", "--tool", choices=AVAILABLE_TOOLS, 
                        action='append', help="Select individual tools to enable")
    parser.add_argument("--on", 
                        action='append', help="Turns on specific tool run_ or check_ option (format tool.check_tool or tool.run_tool, e.g. meidiainfo.run_tool)")
    parser.add_argument("--off", 
                        action='append', help="Turns off specific tool run_ or check_ option (format tool.check_tool or tool.run_tool, e.g. meidiainfo.run_tool)")
    parser.add_argument("-sn","--signalflow", choices=['JPC_AV_SVHS', 'BVH3100'],
                    help="Select signal flow config type (JPC_AV_SVHS or BVH3100)")
    parser.add_argument("-fn","--filename", choices=['jpc', 'bowser'], 
                   help="Select file name config type (jpc or bowser)")
    parser.add_argument("-pp","--printprofile", choices=['all', 'spex', 'checks'], nargs='?', const='all',
                        help="Show config profile(s). Default: all")
    parser.add_argument("-d","--directory", action="store_true", 
                        help="Flag to indicate input is a directory")
    parser.add_argument("-f","--file", action="store_true", 
                        help="Flag to indicate input is a video file")
    parser.add_argument('--gui', action='store_true', 
                        help='Force launch in GUI mode')
    
    # Config export/import arguments
    parser.add_argument('--export-config', 
                    choices=['all', 'spex', 'checks'],
                    help='Export current config(s) to JSON')
    parser.add_argument('--export-file',
                    help='Specify export filename (default: auto-generated)')
    parser.add_argument('--import-config',
                    help='Import configs from JSON file')
    parser.add_argument("--mediaconch-policy",
                    help="Path to custom MediaConch policy XML file")

    args = parser.parse_args()

    input_paths = args.paths if args.paths else []
    source_directories = dir_setup.validate_input_paths(input_paths, args.file)

    selected_profile = edit_config.resolve_config(args.profile, PROFILE_MAPPING)
    sn_config_changes = edit_config.resolve_config(args.signalflow, SIGNALFLOW_MAPPING)
    fn_config_changes = edit_config.resolve_config(args.filename, FILENAME_MAPPING)

    return ParsedArguments(
        source_directories=source_directories,
        selected_profile=selected_profile,
        tool_names=args.tool or [],
        sn_config_changes=sn_config_changes,
        fn_config_changes=fn_config_changes,
        print_config_profile=args.printprofile,
        dry_run_only=args.dryrun,
        tools_on_names=args.on or [],
        tools_off_names=args.off or [],
        gui=args.gui,
        export_config=args.export_config,
        export_file=args.export_file,
        import_config=args.import_config,
        mediaconch_policy=args.mediaconch_policy
    )


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
    video_id
    )

    metadata_differences = processing_mgmt.process_video_metadata(
        video_path, 
        destination_directory, 
        video_id, 
        )

    processing_results = processing_mgmt.process_video_outputs(
        video_path,
        source_directory,
        destination_directory,
        video_id,
        metadata_differences
    )

    logger.debug(f'Please note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!\n')

    # Display final processing banner
    display_processing_banner(video_id)



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


def update_spex_config(config_type: str, profile_name: str):
    spex_config = config_mgr.get_config('spex', SpexConfig)
    
    if config_type == 'signalflow':
        if not isinstance(profile_name, dict):
            logger.critical(f"Invalid signalflow settings: {profile_name}")
            return
            
        for key, value in profile_name.items():
            setattr(spex_config.mediatrace_values.ENCODER_SETTINGS, key, value)
            spex_config.ffmpeg_values['format']['tags']['ENCODER_SETTINGS'][key] = value
        config_mgr.set_config('spex', spex_config)
            
    elif config_type == 'filename':
        if not isinstance(profile_name, dict):
            logger.critical(f"Invalid filename settings: {profile_name}")
            return
            
        updates = {
            "filename_values": profile_name
        }
        # Update and save config
        config_mgr.update_config('spex', updates)
        
    else:
        logger.critical(f"Invalid configuration type: {config_type}")
        return
        
    # Save the last used config
    config_mgr.save_last_used_config('spex')


def run_cli_mode(args):
    print_av_spex_logo()

    # Update checks config
    if args.selected_profile:
        config_mgr.update_config('checks', args.selected_profile)
    if args.tool_names:
        edit_config.apply_by_name(args.tool_names)
        config_mgr.save_last_used_config('checks')
    if args.tools_on_names:
        edit_config.toggle_on(args.tools_on_names)
        config_mgr.save_last_used_config('checks')
    if args.tools_off_names:
        edit_config.toggle_off(args.tools_off_names)
        config_mgr.save_last_used_config('checks')

    if args.mediaconch_policy:
        processing_mgmt.setup_mediaconch_policy(args.mediaconch_policy)

    # Update spex config
    if args.sn_config_changes:
        update_spex_config('signalflow', args.sn_config_changes)
    if args.fn_config_changes:
        update_spex_config('filename', args.fn_config_changes)

    # Handle config I/O operations
    if args.export_config:
        config_types = ['spex', 'checks'] if args.export_config == 'all' else [args.export_config]
        config_io = ConfigIO(config_mgr)
        filename = config_io.save_configs(args.export_file, config_types)
        print(f"Configs exported to: {filename}")
        if args.dry_run_only:
            sys.exit(0)
    
    if args.import_config:
        config_io = ConfigIO(config_mgr)
        config_io.import_configs(args.import_config)
        print(f"Configs imported from: {args.import_config}")

    if args.print_config_profile:
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

    checks_config = config_mgr.get_config('checks', ChecksConfig)
    spex_config = config_mgr.get_config('spex', SpexConfig)

    overall_start_time = time.time()

    process_directories(source_directories)

    print_nmaahc_logo()

    overall_end_time = time.time()

    formatted_overall_time = log_overall_time(overall_start_time, overall_end_time)


def main_gui():
    app = QApplication(sys.argv)  # Create the QApplication instance once
    while True:
        window = MainWindow()
        window.show()
        app.exec()  # Blocks until the GUI window is closed
        source_directories = window.get_source_directories()

        if source_directories:
            run_avspex(source_directories)
        else:
            # If no source directories were selected, exit the loop (quit the app)
            break


def main_cli():
    args = parse_arguments()

    if args.gui:
       main_gui()
    else:
        run_cli_mode(args)
        if args.source_directories:
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

