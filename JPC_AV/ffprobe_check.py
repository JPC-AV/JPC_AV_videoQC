#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json
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
    
    with open(file_path, 'r') as file:
        ffmpeg_data = json.load(file)
    
    # Now you can proceed with the rest of your code
    ffmpeg_output = {}
    
    ffmpeg_output['ffmpeg_video'] = ffmpeg_data['streams'][0]
    ffmpeg_output['ffmpeg_audio'] = ffmpeg_data['streams'][1]
    ffmpeg_output['format'] = ffmpeg_data['format']

    differences = []
    # Create empty list, "differences"
    for expected_key, expected_value in expected_video_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in ffmpeg_output['ffmpeg_video']:
        # if the key in the dictionary "General"
            actual_value = str(ffmpeg_output['ffmpeg_video'][expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                differences.append(f"{expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_value}\n")
                # append this string to the list "differences"
    
    for expected_key, expected_value in expected_audio_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in ffmpeg_output['ffmpeg_audio']:
        # if the key in the dictionary "Video"
            actual_value = str(ffmpeg_output['ffmpeg_audio'][expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                differences.append(f"{expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_value}\n")
                # append this string to the list "differences"

    for expected_key, expected_value in expected_format_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key not in (ffmpeg_output['format']):
            differences.append(f"metadata field: {expected_key} does not exist") 
        elif len(ffmpeg_output['format'][expected_key]) == 0:
        # count the values in the nested dictionary "General" with 'len', if the values are zero, then:
            differences.append(f"General: {expected_key} is empty")
            # append this string to the list "differences"
        
    if expected_format_values['format_name'] != str(ffmpeg_output['format']['format_name']).replace(',', ' '):
        differences.append(f"Encoder setting 'format_name'\n\tExpected: {expected_format_values['format_name']}\n\tActual: {ffmpeg_output['format']['format_name']}\n")
        # append this string to the list "differences"
    if expected_format_values['format_long_name'] != ffmpeg_output['format']['format_long_name']:
        differences.append(f"Encoder setting 'format_long_name'\n\tExpected: {expected_format_values['format_name']}\n\tActual: {ffmpeg_output['format']['format_name']}\n")
        # append this string to the list "differences"
        
    encoder_settings = ffmpeg_output['format']['tags']['ENCODER_SETTINGS']
    settings_dict1, settings_dict2, settings_dict3 = parse_encoder_settings(encoder_settings)
    for expected_key, expected_value in expected_settings_values_1.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in settings_dict1:
        # if the key in the dictionary "Video"
            actual_setting = str(settings_dict1[expected_key]).strip()
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_setting != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                differences.append(f"Encoder setting {expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_setting}\n")
                # append this string to the list "differences"
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
                if actual_setting != expected_value:
                # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                    differences.append(f"Encoder setting {expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_setting}\n")
                    # append this string to the list "differences"
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
                if actual_setting != expected_value:
                # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                    differences.append(f"Encoder setting {expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_setting}\n")
                    # append this string to the list "differences"
    
    if not differences:
    # if the list "differences" is empty, then
        logger.debug("All specified fields and values found in the ffmpeg output.")
    else:
    # if the list "differences" is not empty, then
        logging.critical("Some specified ffmpeg fields or values are missing or don't match:")
        for diff in differences:
            logging.critical(f'\n\t{diff}')

# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ffprobe_json_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    parse_ffprobe(file_path)
    #runs the function "parse_mediainfo" on the file assigned to the variable "file_path"