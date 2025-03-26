#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from typing import Dict, Any, Optional

from ..utils.log_setup import logger
from ..utils.config_setup import ChecksConfig, SpexConfig
from ..utils.config_manager import ConfigManager

config_mgr = ConfigManager()
checks_config = config_mgr.get_config('checks', ChecksConfig)
spex_config = config_mgr.get_config('spex', SpexConfig)


## creates the function "parse_mediainfo" which takes the argument "file_path" which is intended to be a mediainfo -f text file
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_mediainfo(file_path):
    section_data = parse_mediainfo_json(file_path)
    mediainfo_differences = check_mediainfo_spex(section_data)

    return mediainfo_differences


def parse_mediainfo_json(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a MediaInfo JSON file and extract relevant information organized by section.
    
    Args:
        file_path: Path to the MediaInfo JSON file
        
    Returns:
        Dictionary with General, Video, and Audio sections containing key-value pairs
    """
    section_data = {"General": {}, "Video": {}, "Audio": {}}
    
    if not os.path.exists(file_path):
        logger.critical(f"Cannot perform MediaInfo check! No such file: {file_path}")
        return section_data

    try:
        with open(file_path, 'r') as file:
            mediainfo = json.load(file)
            
            # Extract track information from the JSON structure
            if 'media' in mediainfo and 'track' in mediainfo['media']:
                tracks = mediainfo['media']['track']
                
                for track in tracks:
                    track_type = track.get('@type')
                    
                    if track_type == 'General':
                        section_data["General"] = extract_general_data(track)
                    elif track_type == 'Video':
                        section_data["Video"] = extract_video_data(track)
                    elif track_type == 'Audio':
                        section_data["Audio"] = extract_audio_data(track)
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        
    return section_data

def extract_general_data(track: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant General track data"""
    general_data = {}
    
    # Map directly to fields in MediainfoGeneralValues
    fields_to_extract = [
        "FileExtension",
        "Format",
        "OverallBitRate_Mode"
    ]
    
    for field in fields_to_extract:
        if field in track:
            general_data[field] = track[field]
    
    # Handle extra fields in General track
    if "extra" in track:
        extra = track["extra"]
        if "ErrorDetectionType" in extra:
            general_data["ErrorDetectionType"] = extra["ErrorDetectionType"]
    
    return general_data

def extract_video_data(track: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant Video track data"""
    video_data = {}
    
    # Map directly to fields in MediainfoVideoValues
    fields_to_extract = [
        "Format",
        "Format_Settings_GOP",
        "CodecID",
        "Width",
        "Height",
        "PixelAspectRatio",
        "DisplayAspectRatio",
        "FrameRate_Mode_String",
        "FrameRate",
        "Standard",
        "ColorSpace",
        "ChromaSubsampling",
        "BitDepth",
        "ScanType",
        "ScanOrder",
        "Compression_Mode",
        "colour_primaries",
        "colour_primaries_Source",
        "transfer_characteristics",
        "transfer_characteristics_Source",
        "matrix_coefficients"
    ]
    
    for field in fields_to_extract:
        if field in track:
            video_data[field] = track[field]
    
    # Handle special cases from extra field
    if "extra" in track:
        extra = track["extra"]
        # Handle MaxSlicesCount - note the case difference between JSON and expected field name
        if "MaxSlicesCount" in extra:
            video_data["MaxSlicesCount"] = extra["MaxSlicesCount"]
        # Handle ErrorDetectionType
        if "ErrorDetectionType" in extra:
            video_data["ErrorDetectionType"] = extra["ErrorDetectionType"]
    
    return video_data

def extract_audio_data(track: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant Audio track data"""
    audio_data = {}
    
    # Direct mapping fields
    direct_fields = [
        "Format",
        "Channels",
        "SamplingRate",
        "BitDepth",
        "Compression_Mode"
    ]
    
    for field in direct_fields:
        if field in track:
            audio_data[field] = track[field]

    return audio_data

def check_mediainfo_spex(section_data):
    """
    Compare MediaInfo values with expected specifications.
    
    Args:
        section_data: Dictionary with General, Video, and Audio sections
        
    Returns:
        Dictionary of differences between actual and expected values
    """
    # Safely get expected values, defaulting to empty dictionaries if not present
    expected_general = getattr(spex_config.mediainfo_values, 'expected_general', {})
    expected_video = getattr(spex_config.mediainfo_values, 'expected_video', {})
    expected_audio = getattr(spex_config.mediainfo_values, 'expected_audio', {})

    mediainfo_differences = {}

    # Check General section
    if "General" in section_data:
        for expected_key, expected_value in expected_general.items():
            if expected_key in section_data["General"]:
                actual_value = section_data["General"][expected_key]
                # Ensure expected_value is always a list for comparison
                expected_list = expected_value if isinstance(expected_value, list) else [expected_value]
                if actual_value not in expected_list:
                    mediainfo_differences[expected_key] = [actual_value, expected_value]
    
    # Check Video section
    if "Video" in section_data:
        for expected_key, expected_value in expected_video.items():
            if expected_key in section_data["Video"]:
                actual_value = section_data["Video"][expected_key]
                # Ensure expected_value is always a list for comparison
                expected_list = expected_value if isinstance(expected_value, list) else [expected_value]
                if actual_value not in expected_list:
                    mediainfo_differences[expected_key] = [actual_value, expected_value]
    
    # Check Audio section
    if "Audio" in section_data:
        for expected_key, expected_value in expected_audio.items():
            if expected_key in section_data["Audio"]:
                actual_value = section_data["Audio"][expected_key]
                # Ensure expected_value is always a list for comparison
                expected_list = expected_value if isinstance(expected_value, list) else [expected_value]
                if actual_value not in expected_list:
                    mediainfo_differences[expected_key] = [actual_value, expected_value]

    # Log results
    if not mediainfo_differences:
        logger.info("All specified fields and values found in the MediaInfo output.\n")
    else:
        logger.critical("Some specified MediaInfo fields or values are missing or don't match:")
        for mi_key, values in mediainfo_differences.items():
            actual_value, expected_value = values
            logger.critical(f"Metadata field {mi_key} has a value of: {actual_value}\nThe expected value is: {expected_value}")
        logger.debug("")  # adding a space after results if there are failures


    return mediainfo_differences


# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <mediainfo_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    mediainfo_differences = parse_mediainfo(file_path)
    if mediainfo_differences:
        for diff in mediainfo_differences:
            logger.critical(f"\t{diff}")