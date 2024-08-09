#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from ..utils.log_setup import logger
from ..utils.find_config import config_path

## creates the function "parse_mediainfo" which takes the argument "file_path" which is intended to be a mediainfo -f text file
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_mediainfo(file_path):
    expected_general = config_path.config_dict['mediainfo_values']['expected_general']
    expected_video = config_path.config_dict['mediainfo_values']['expected_video']
    expected_audio = config_path.config_dict['mediainfo_values']['expected_audio']

    section_data = {}
    # creates empty dictionary "section_data"
    # this dictionary will actually store 3 separate dictionaries inside of it (called a "nested dictionary"), one for each section
    section_data["General"] = {}
    # nested dicitonary for storing data from "General" section
    section_data["Video"] = {}
    # nested dicitonary for storing data from "Video" section
    section_data["Audio"] = {}
    # nested dictionary for storing data from "Audio" section

    ## Explanation of for loop below:
    # the mediainfo field and value are then assigned to the current section's dictionary, which is stored within the section_data dictionary
    
    if not os.path.exists(file_path):
        logger.critical(f"Cannot perform MediaInfo check!No such file: {file_path}")
        return
    
    with open(file_path, 'r') as file:
    # open mediainfo text file as variable "file"
        for line in iter(lambda: file.readline().rstrip(), 'Video'):
        # for each line in mediainfo text file, read the line, strip out any blank space, and stop when you reach 'Video'
        # I found this technique here: https://stackoverflow.com/questions/27135499/read-file-until-specific-line-in-python
            if line.startswith("General"):
            # if the line starts with "General"
                continue
                # do nothing
            elif line:
            # for every other line (until 'Video'), do:
                key, value = [x.strip() for x in line.split(":", 1)]
                # assign variable "key" to string before ":" and variable "value" to string after ":"
                section_data["General"][key] = value
                # add key: value pair to nested dictionary 
        for line in file:
        # For the next lines in the file, do this:
        # (This "for" loop will pick up where the previous one ended, the line right after 'Video')
            if ":" in line:
            # if ":" is in the line (basically, if the line is not 'Audio')
                key, value = [x.strip() for x in line.split(":", 1)]
                # assign variable "key" to string before ":" and variable "value" to string after ":"
                if key == 'Frame rate':
                    value = value.split(" (", 1)[0]
                section_data["Video"][key] = value
                # add key: value pair to nested dictionary
            elif line.startswith("Audio"):
                break
                # if line starts with "Audio" stop
                # Not sure why, but the 'lambda' technique was causing a key error for this section, either on the blank line before 'Audio' or on 'Audio'.
                # After a lot of troubleshooting, just decided to do it this way instead
        for line in file:
        # For the next lines in the file, do this:
        # (This "for" loop will pick up where the previous one ended, the line right after 'Audio')
        # https://stackoverflow.com/questions/27805919/how-to-only-read-lines-in-a-text-file-after-a-certain-string
            if ":" in line:
                key, value = [x.strip() for x in line.split(":", 1)]
                # assign variable "key" to string before ":" and variable "value" to string after ":"
                section_data["Audio"][key] = value
                # add key: value pair to nested dictionary

    ## Explanation of the loops below:
    # The loops below assign the variables "expected_key" and "expected_value" to the key:value pairs in the "expected" dictionaries defined at the beginning of the function
    # the variable "actual_value" is used to define the value to the key that matches 'expected_key' in the section_data nested dictionaries (defined in the loop above)
    # if the actual_value variable and the expected_value variable don't match, then a string stating both values is append to a list called "mediainfo_differences"

    mediainfo_differences = {}
    # Create empty list, "mediainfo_differences"
    for expected_key, expected_value in expected_general.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in section_data["General"]:
        # if the key in the dictionary "General"
            actual_value = section_data["General"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                mediainfo_differences[expected_key] = [actual_value, expected_value]
    
    for expected_key, expected_value in expected_video.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in section_data["Video"]:
        # if the key in the dictionary "Video"
            actual_value = section_data["Video"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                 mediainfo_differences[expected_key] = [actual_value, expected_value]

    for expected_key, expected_value in expected_audio.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key in section_data["Audio"]:
        # if the key in the dictionary "Audio"
            actual_value = section_data["Audio"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Audio"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
                mediainfo_differences[expected_key] = [actual_value, expected_value]
    
    if not mediainfo_differences:
    # if the list "mediainfo_differences" is empty, then
        logger.info("All specified fields and values found in the MediaInfo output.")
    else:
    # if the list "mediainfo_differences" is not empty, then
        logger.critical(f"Some specified MediaInfo fields or values are missing or don't match:")
        for mi_key, values in mediainfo_differences.items():
            actual_value, expected_value = values
            logger.critical(f"Metadata field {mi_key} has a value of: {actual_value}The expected value is: {expected_value}")
    
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