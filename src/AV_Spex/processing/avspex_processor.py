#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from art import art, text2art

from ..processing.processing_mgmt import ProcessingManager
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
    def __init__(self, signals=None):
        self.signals = signals
        self.config_mgr = ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.spex_config = self.config_mgr.get_config('spex', SpexConfig)
        self._cancelled = False
        self._cancel_emitted = False 

    def cancel(self):
        self._cancelled = True

    def check_cancelled(self):
        """Check if processing was cancelled and emit signal if needed"""
        if self._cancelled and self.signals and not self._cancel_emitted:
            self.signals.cancelled.emit()
            self._cancel_emitted = True
        return self._cancelled

    def initialize(self):
        """Check all prerequisites before processing"""
        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.status_update.emit("Checking Python version...")
        check_py_version()
        
        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.status_update.emit("Checking required dependencies...")
        
        total_commands = len(required_commands)
        for idx, command in enumerate(required_commands, 1):
            if self.check_cancelled():
                return False

            if self.signals:
                self.signals.status_update.emit(f"Finding {command} ({idx}/{total_commands})...")
                self.signals.progress.emit(idx, total_commands)
                
            if not check_external_dependency(command):
                error_msg = f"Error: {command} not found. Please install it."
                if self.signals:
                    self.signals.error.emit(error_msg)
                raise RuntimeError(error_msg)
        
        if self.signals:
            self.signals.status_update.emit("All dependencies identified successfully.")
        
        return True

    def process_directories(self, source_directories):
        if self.check_cancelled():
            return False

        overall_start_time = time.time()
        total_dirs = len(source_directories)

        for idx, source_directory in enumerate(source_directories, 1):
            if self.check_cancelled():
                return False

            if self.signals:
                self.signals.progress.emit(idx, total_dirs)
                self.signals.status_update.emit(f"Processing directory {idx}/{total_dirs}: {source_directory}")
            
            source_directory = os.path.normpath(source_directory)
            if not self.process_single_directory(source_directory):
                return False

        overall_end_time = time.time()
        return log_overall_time(overall_start_time, overall_end_time)

    def process_single_directory(self, source_directory):
        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.status_update.emit(f"Initializing directory: {source_directory}")

        init_dir_result = dir_setup.initialize_directory(source_directory)
        if init_dir_result is None:
            if self.signals:
                self.signals.error.emit(f"Failed to initialize directory: {source_directory}")
            return False

        video_path, video_id, destination_directory, access_file_found = init_dir_result
        processing_mgmt = ProcessingManager(signals=self.signals, check_cancelled_fn=self.check_cancelled)

        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.tool_started.emit("Fixity...")

        processing_mgmt.process_fixity(source_directory, video_path, video_id)

        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.tool_completed.emit("Fixity processing complete")
            self.signals.tool_started.emit("MediaConch...")

        mediaconch_results = processing_mgmt.validate_video_with_mediaconch(
            video_path, destination_directory, video_id
        )

        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.tool_completed.emit("MediaConch validation complete")
            self.signals.tool_started.emit("video metadata tools...")
        
        metadata_differences = processing_mgmt.process_video_metadata(
            video_path, destination_directory, video_id
        )

        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.tool_completed.emit("Metadata tools complete")
            self.signals.tool_started.emit("Output processing...")
        
        processing_results = processing_mgmt.process_video_outputs(
            video_path, source_directory, destination_directory,
            video_id, metadata_differences
        )

        if self.check_cancelled():
            return False

        if self.signals:
            self.signals.tool_completed.emit("Outputs complete")
        
        logger.debug('Please note that any warnings on metadata are just used to help any issues with your file. If they are not relevant at this point in your workflow, just ignore this. Thanks!\n')
        
        display_processing_banner(video_id)
        return True