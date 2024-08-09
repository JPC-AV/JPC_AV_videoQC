#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import logging
import json
from ..utils.log_setup import logger
from ..utils.find_config import config_path

## creates the function 'parse_exiftool' which takes the argument 'file_path' 
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_ffprobe(file_path):
    # creates a dictionary of expected keys and values
    expected_video_values = config_path.config_dict['ffmpeg_values']['video_stream']
    expected_audio_values = config_path.config_dict['ffmpeg_values']['audio_stream']
    expected_format_values = config_path.config_dict['ffmpeg_values']['format']
    expected_settings_values = config_path.config_dict['ffmpeg_values']['format']['tags']['ENCODER_SETTINGS']
    
    if not os.path.exists(file_path):
        logger.critical(f"Cannot perform ffprobe check!No such file: {file_path}")
        return

    with open(file_path, 'r') as file:
        ffmpeg_data = json.load(file)
    
    # Now you can proceed with the rest of your code
    ffmpeg_output = {}
    
    ffmpeg_output['ffmpeg_video'] = ffmpeg_data['streams'][0]
    ffmpeg_output['ffmpeg_audio'] = ffmpeg_data['streams'][1]
    ffmpeg_output['format'] = ffmpeg_data['format']

    ffprobe_differences = {}
    # Create empty list, "ffprobe_differences"
    for expected_key, expected_value in expected_video_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in ffmpeg_output['ffmpeg_video']:
        # if the key in the dictionary "General"
            actual_value = str(ffmpeg_output['ffmpeg_video'][expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                ffprobe_differences[expected_key] = [actual_value, expected_value]
    
    for expected_key, expected_value in expected_audio_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in ffmpeg_output['ffmpeg_audio']:
        # if the key in the dictionary "Video"
            actual_value = str(ffmpeg_output['ffmpeg_audio'][expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                ffprobe_differences[expected_key] = [actual_value, expected_value]
    
    for expected_key, expected_value in expected_format_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key not in (ffmpeg_output['format']):
            ffprobe_differences[expected_key] = ['metadata field not found', '']
        elif len(ffmpeg_output['format'][expected_key]) == 0:
        # count the values in the nested dictionary "format" with 'len', if the values are zero, then:
            ffprobe_differences[expected_key] = ['no metadata value found', '']
        
    if expected_format_values['format_name'] not in str(ffmpeg_output['format']['format_name']).replace(',', ' '):
        ffprobe_differences["Encoder setting 'format_name'"] = [ffmpeg_output['format']['format_name'], expected_format_values['format_name']]
    if expected_format_values['format_long_name'] not in ffmpeg_output['format']['format_long_name']:
        ffprobe_differences["Encoder setting 'format_long_name'"] = [ffmpeg_output['format']['format_long_name'], expected_format_values['format_long_name']]
        
    if 'ENCODER_SETTINGS' in ffmpeg_output['format']['tags']:
        # initialize variables
        encoder_settings_string = ffmpeg_output['format']['tags']['ENCODER_SETTINGS']
        # split string into list using semicolons as separators. I find reg expression confusing. For reference:
            # r: Indicates a raw string, where backslashes are treated literally (important for regular expressions).
            # \s*: Matches zero or more whitespace characters (spaces, tabs, newlines, etc.).
            # ;: Matches a semicolon character.
            # \s*: Again, matches zero or more whitespace characters.
        encoder_settings_list = re.split(r'\s*;\s*', encoder_settings_string)
        sn_strings = ["SN ", "SN-", "SN##"]
        encoder_settings_dict = {}
        for encoder_settings_device in encoder_settings_list:
            # splits the string into a list based on either colons or commas, ignoring any surrounding whitespace
                # r: Indicates a raw string literal, where backslashes are treated as literal characters.
                # \s*: Matches zero or more whitespace characters (space, tab, newline, etc.).
                # :: Matches a colon character.
                # |: Represents an "OR" condition, meaning either the pattern to the left or the pattern to the right can match.
                # ,: Matches a comma character.
            device_field_name, *device_subfields_w_values = re.split(r'\s*:\s*|\s*,\s*', encoder_settings_device)
            # The first element of the resulting list is assigned to device_field_name
            # The remaining elements of the list (if any) are packed into the list device_subfields_w_values
            encoder_settings_dict[device_field_name] = device_subfields_w_values
        for expected_key, expected_value in expected_settings_values.items():
        # defines variables "expected_key" and "expected_value" to the dictionary "expected_settings_values"
                if expected_key not in encoder_settings_dict:
                    # append this string to the list "ffprobe_differences"
                    ffprobe_differences[f"Encoder setting field {expected_key}"] = ['metadata field not found', '']
                elif set(encoder_settings_dict[expected_key]) != set(expected_value):
                # if the number of items in the "device" field do not match the number in the config, then: 
                    ffprobe_differences[expected_key] = [encoder_settings_dict[expected_key], expected_value]
    else:
        ffprobe_differences["Encoder Settings"] = ['No Encoder Settings found, No Signal Flow data embedded', '']

    if not ffprobe_differences:
        # if the list "ffprobe_differences" is empty, then
        logger.info("All specified fields and values found in the ffprobe output.\n")
    else:
        # if the list "ffprobe_differences" is not empty, then
        logger.critical(f"Some specified ffprobe fields or values are missing or don't match:")
        for ffprobe_key, values in ffprobe_differences.items():
            actual_value, expected_value = values
            if ffprobe_key == 'ENCODER_SETTINGS':
            # This exception is for if there are no encoder settings embedded (cleaner output)
                logger.critical(f"{actual_value}")
            elif expected_value == "":
             # This exception is for if there are missing subfields inside encoder settings (cleaner output)
                logger.critical(f"{ffprobe_key} {actual_value}")
            else:    
                logger.critical(f"Metadata field {ffprobe_key} has a value of: {actual_value}The expected value is: {expected_value}")
        logger.debug(f'')


# Only execute if this file is run directly, not imported
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ffprobe_json_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    ffprobe_differences = parse_ffprobe(file_path)
    if ffprobe_differences:
        for diff in ffprobe_differences:
            logger.critical(f"\t{diff}")