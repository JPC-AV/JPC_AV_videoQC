#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from art import art, text2art

from ..processing import processing_mgmt
from ..processing import run_tools
from ..utils import dir_setup
from ..utils import edit_config
from ..utils.log_setup import logger
from ..utils.deps_setup import required_commands, check_external_dependency, check_py_version
from ..utils.setup_config import ChecksConfig, SpexConfig
from ..utils.config_manager import ConfigManager
from ..utils.config_io import ConfigIO

config_mgr = ConfigManager()

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

class AVSpexProcessor:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.spex_config = self.config_mgr.get_config('spex', SpexConfig)
        
    def initialize(self):
        """Check all prerequisites before processing"""
        check_py_version()
        
        for command in required_commands:
            if not check_external_dependency(command):
                raise RuntimeError(f"Error: {command} not found. Please install it.")
        
        return True
        
    def process_directories(self, source_directories):
        """Main processing method"""
        overall_start_time = time.time()
        
        for source_directory in source_directories:
            source_directory = os.path.normpath(source_directory)
            self.process_single_directory(source_directory)
            
        print_nmaahc_logo()
        
        overall_end_time = time.time()
        return log_overall_time(overall_start_time, overall_end_time)

    def process_single_directory(self, source_directory):
        display_processing_banner()
        
        init_dir_result = dir_setup.initialize_directory(source_directory)
        if init_dir_result is None:
            return

        video_path, video_id, destination_directory, access_file_found = init_dir_result
        
        processing_mgmt.process_fixity(source_directory, video_path, video_id)
        
        mediaconch_results = processing_mgmt.validate_video_with_mediaconch(
            video_path, destination_directory, video_id
        )
        
        metadata_differences = processing_mgmt.process_video_metadata(
            video_path, destination_directory, video_id
        )
        
        processing_results = processing_mgmt.process_video_outputs(
            video_path, source_directory, destination_directory,
            video_id, metadata_differences
        )
        
        logger.debug('Please note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!\n')
        
        display_processing_banner(video_id)