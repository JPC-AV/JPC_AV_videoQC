#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from log_config import logger
import os
import sys

## creates the function "parse_mediainfo" which takes the argument "file_path" which is intended to be a mediainfo -f text file
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_mediainfo(file_path):
    # creates a dictionary of expected keys and values for the mediainfo output section "General"
    expected_general = {
        "File extension": "mkv",
        "Format": "Matroska",
        "Overall bit rate mode": "Variable",
    }
    # creates a dictionary of expected keys and values for the mediainfo output section "Video"
    expected_video = {
        "Format": "FFV1",
        "Format settings, GOP": "N=1",
        "Codec ID": "V_MS/VFW/FOURCC / FFV1",
        "Width": "720 pixels",
        "Height": "486 pixels",
        "Pixel aspect ratio": "0.900",
        "Display aspect ratio": "4:3",
        "Frame rate mode": "Constant",
        "Frame rate": "29.970 (30000/1001) FPS",
        "Standard": "NTSC",
        "Color space": "YUV",
        "Chroma subsampling": "4:2:2",
        "Bit depth": "10 bits",
        "Scan type": "Interlaced",
        "Scan order": "Bottom Field First",
        "Compression mode": "Lossless",
        "Color primaries": "BT.601 NTSC",
        "colour_primaries_Source": "Container",
        "Transfer characteristics": "BT.709",
        "transfer_characteristics_Source": "Container",
        "Matrix coefficients": "BT.601",
        "MaxSlicesCount": "24",
        "ErrorDetectionType": "Per slice",
    }
    # creates a dictionary of expected keys and values for the mediainfo output section "Audio"
    expected_audio = {
        "Format": ["FLAC", "PCM"],
        "Channel(s)": "2 channels",
        "Sampling rate": "48.0 kHz",
        "Bit depth": "24 bits",
        "Compression mode": "Lossless",
    }

    # creates a list of fields to check, but only to check that the fiels is not empty
    expected_custom_fields = {
        "Title": "",
        "Encoded by": "",
        "Description": "",
        "Encoding settings": "",
        "ORIGINAL MEDIA TYPE": "",
    }

    section_data = {}
    # creates empty dictionary "section_data"
    # this dictionary will actually store 3 separate dictionaries inside of it (called a "nested dictionary"), one for each section
    section_data["General"] = {}
    # nested dicitonary for storing data from "General" section
    section_data["Video"] = {}
    # nested dicitonary for storing data from "Video" section
    section_data["Audio"] = {}
    # nested dicitonary for storing data from "Audio" section

    ## Explination of for loop below:
    # the mediainfo field and value are then assigned to the current section's dictionary, which is stored within the section_data dictionary
    
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

    ## Explination of the loops below:
    # The loops below assign the variables "expected_key" and "expected_value" to the key:value pairs in the "expected" dictionaries defined at the beginning of the function
    # the variable "actual_value" is used to define the value to the key that matches 'expected_key' in the section_data nested dictionaries (defined in the loop above)
    # if the actual_value variable and the expected_value variable don't match, then a string stating both values is appened to a list called "differences"

    differences = []
    # Create empty list, "differences"
    for expected_key, expected_value in expected_general.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in section_data["General"]:
        # if the key in the dictionary "General"
            actual_value = section_data["General"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                differences.append(f"General: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"
    
    for expected_key, expected_value in expected_video.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in section_data["Video"]:
        # if the key in the dictionary "Video"
            actual_value = section_data["Video"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                differences.append(f"Video: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"

    for expected_key, expected_value in expected_audio.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key in section_data["Audio"]:
        # if the key in the dictionary "Audio"
            actual_value = section_data["Audio"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Audio"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value not in expected_value:
                differences.append(f"Audio: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"

    for expected_key, expected_value in expected_custom_fields.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key not in (section_data["General"]):
            differences.append(f"metadata field in General: {expected_key} does not exist") 
        elif len(section_data["General"][expected_key]) == 0:
        # count the values in the nested dictionary "General" with 'len', if the values are zero, then:
            differences.append(f"General: {expected_key} is empty")
            # append this string to the list "differences"
    
    if not differences:
    # if the list "differences" is empty, then
        logger.debug("All specified fields and values found in the MediaInfo output.")
    else:
    # if the list "differences" is not empty, then
        logging.critical("Some specified MediaInfo fields or values are missing or don't match:")
        for diff in differences:
            logging.critical(f'\n\t{diff}')

if len(sys.argv) != 2:
    print("Usage: python script.py <mediainfo_file>")
    sys.exit(1)

file_path = sys.argv[1]

if not os.path.isfile(file_path):
    print(f"Error: {file_path} is not a valid file.")
    sys.exit(1)

parse_mediainfo(file_path)
#runs the function "parse_mediainfo" on the file assigned to the variable "file_path"
