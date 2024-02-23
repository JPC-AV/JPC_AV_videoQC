#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json
import csv
from log_setup import logger
from find_config import config_path
from encoder_settings_check import parse_encoder_settings

## creates the function 'parse_exiftool' which takes the argument 'file_path' 
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_ffprobe(file_path):
    # creates a dictionary of expected keys and values
    expected_video_values = config_path.config_dict['ffmpeg_values']['video_stream']
    expected_audio_values = config_path.config_dict['ffmpeg_values']['audio_stream']
    expected_format_values = config_path.config_dict['ffmpeg_values']['format']
    expected_settings_values_1 = config_path.config_dict['ffmpeg_values']['format']['tags']['ENCODER_SETTINGS']['settings_1']
    expected_settings_values_2 = config_path.config_dict['ffmpeg_values']['format']['tags']['ENCODER_SETTINGS']['settings_2']
    expected_settings_values_3 = config_path.config_dict['ffmpeg_values']['format']['tags']['ENCODER_SETTINGS']['settings_3']
    
    if not os.path.exists(file_path):
        logger.critical(f"\nCannot perform ffprobe check!\nNo such file: {file_path}")
        return

    with open(file_path, 'r') as file:
        ffmpeg_data = json.load(file)
    
    # Now you can proceed with the rest of your code
    ffmpeg_output = {}
    
    ffmpeg_output['ffmpeg_video'] = ffmpeg_data['streams'][0]
    ffmpeg_output['ffmpeg_audio'] = ffmpeg_data['streams'][1]
    ffmpeg_output['format'] = ffmpeg_data['format']

    ffprobe_differences = []
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
                ffprobe_differences.append(f"Metadata field {expected_key} has a value of: {actual_value}\nThe expected value is: {expected_value}\n")
                # append this string to the list "ffprobe_differences"
    
    for expected_key, expected_value in expected_audio_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in ffmpeg_output['ffmpeg_audio']:
        # if the key in the dictionary "Video"
            actual_value = str(ffmpeg_output['ffmpeg_audio'][expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                ffprobe_differences.append(f"Metadata field {expected_key} has a value of: {actual_value}\nThe expected value is: {expected_value}\n")
                # append this string to the list "ffprobe_differences"

    
    for expected_key, expected_value in expected_format_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key not in (ffmpeg_output['format']):
            ffprobe_differences.append(f"metadata field: {expected_key} does not exist\n") 
        elif len(ffmpeg_output['format'][expected_key]) == 0:
        # count the values in the nested dictionary "General" with 'len', if the values are zero, then:
            ffprobe_differences.append(f"General: {expected_key} is empty\n")
            # append this string to the list "ffprobe_differences"
        
    if expected_format_values['format_name'] not in str(ffmpeg_output['format']['format_name']).replace(',', ' '):
        ffprobe_differences.append(f"Encoder setting 'format_name' has a value of: {ffmpeg_output['format']['format_name']}\nThe expected value is: {expected_format_values['format_name']}\n")
        # append this string to the list "ffprobe_differences"
    if expected_format_values['format_long_name'] not in ffmpeg_output['format']['format_long_name']:
        ffprobe_differences.append(f"Encoder setting 'format_long_name' has a value of: {ffmpeg_output['format']['format_long_name']}\nThe expected value is: {expected_format_values['format_long_name']}\n")
        # append this string to the list "ffprobe_differences"
        
    if 'ENCODER_SETTINGS' in ffmpeg_output['format']['tags']:
        encoder_settings = ffmpeg_output['format']['tags']['ENCODER_SETTINGS']
        settings_dict1, settings_dict2, settings_dict3 = parse_encoder_settings(encoder_settings)
        for expected_key, expected_value in expected_settings_values_1.items():
        # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
            if expected_key in settings_dict1:
            # if the key in the dictionary "Video"
                actual_setting = str(settings_dict1[expected_key]).strip()
                # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
                # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
                if actual_setting not in expected_value:
                # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                    ffprobe_differences.append(f"Encoder setting {expected_key} has a value of: {actual_setting}\nThe expected value is: {expected_value}\n")
                    # append this string to the list "ffprobe_differences"
        for expected_key, expected_value in expected_settings_values_2.items():
        # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
            if expected_key in settings_dict2:
            # if the key in the dictionary "Video"
                if expected_key == 'T':
                    actual_setting = ( ", ".join(repr(e) for e in settings_dict1[expected_key]))
                    # https://stackoverflow.com/questions/13207697/how-to-remove-square-brackets-from-list-in-python
                else:
                    actual_setting = settings_dict2[expected_key]
                    # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
                    # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
                    if actual_setting not in expected_value:
                    # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                        ffprobe_differences.append(f"Encoder setting {expected_key} has a value of: {actual_setting}\nThe expected value is: {expected_value}\n")
                        # append this string to the list "ffprobe_differences"
        for expected_key, expected_value in expected_settings_values_3.items():
        # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
            if expected_key in settings_dict3:
            # if the key in the dictionary "Video"
                if expected_key == 'W':
                    actual_setting = ( ", ".join(repr(e) for e in settings_dict3[expected_key]))
                else:
                    actual_setting = settings_dict3[expected_key]
                    # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
                    # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
                    if actual_setting not in expected_value:
                    # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                        ffprobe_differences.append(f"Encoder setting {expected_key} has a value of: {actual_setting}\nThe expected value is: {expected_value}\n")
                        # append this string to the list "ffprobe_differences"
    else:
        logger.critical(f"No 'encoder settings' in ffprobe output\n")

    if not ffprobe_differences:
        # if the list "ffprobe_differences" is empty, then
        logger.info("All specified fields and values found in the ffprobe output.")
    else:
        # if the list "ffprobe_differences" is not empty, then
        logger.critical("Some specified ffprobe fields or values are missing or don't match:")
        for diff in ffprobe_differences:
            logger.critical(f'{diff}')


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
            logger.critical(f"\n\t{diff}")