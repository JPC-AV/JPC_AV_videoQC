#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from log_setup import logger

## This is script is for parsing the customized "Encoder settings" containing transfer information 
# The Encoder Settings value that are expected (stored in cofing/config.yaml) are based on the Encoder Settings value of JPC_AV_05000:
# "ENCODER_SETTINGS": "O=VHS, C=Color, S=Analog, VS= NTSC, F=24, A=4:3, R=640×480, T=Sony SVO-5800, O=FFV1mkv, C=Color, V=Composite, S=Analog Stereo, F=24, A=4:3, W=10-bit, R=640×480, M=YUV422p10, T=Blackmagic UltraStudio 4K Mini SN123456, ffmpeg vrecord; in-house, O=FFV1mkv, W=10-bit, R640x480, MYUV422p10 N=AJ Lawrence"
# Because the sub fields within Encoder Settings use some of the same identifiers (for example "O" may equal either "SVHS" or "FFV1mkv"), the identifiers need to be split into sublists: settings_dict1, settings_dict2, settings_dict3

# The parse_encoder_settings function is intended to be passed to the parse_ffprobe function
# parse_ffprobe reads the field:value pairs of a JSON formatted ffprobe output and assigns the value of the filed format/tags/encoder settings to the variable encoder_settings
def parse_encoder_settings(encoder_settings):
    # Splitting the settings string on "," into key:value pairs
    settings_list = [pair.strip() for pair in encoder_settings.split(",")]

    # By iterating through the key:value pairs of ENCODER SETTINGS stored in settings_list, 3 subsists can be created, each of the 3 lists starting with '0=' to avoid duplicate identifiers of metadata fields
    sublists = []
    # sublists will be a nested list, it will hold 3 separate lists for the 3 sections within encoder settings
    current_sublist = []
    # current_sublist will temporarily hold a list at a time, before that list is appended to the nested list subsists
    
    for pair in settings_list:
    # Iterate through the key:value pairs
        if 'O=' in pair:
        # if pair begins with "0="
            if current_sublist:
                sublists.append(current_sublist)
                # If current pair is "0=" and current_sublist is populated, append active list to the nested list 'subsists'
            current_sublist = [pair]
            # If current pair is "0=" and current_sublist is not populated, start current_sublist with pair
        else:
            current_sublist.append(pair)
            # If current pair is not "0=" append pair to current_sublist

    sublists.append(current_sublist)
    # appends the last sublists to the nested list sublists

    # Assign each of the lists within the nested list 'sublists' to a dictionary of key:value pairs split on the '=' character
    settings_dict1 = {}
    for pair in sublists[0]:
        key, value = pair.split("=")
        settings_dict1[key] = value

    # The field identifier 'T' in the 2nd list of encoder settings holds multiple values, but the values are separated by a ',' 
    # for example: 'T=Blackmagic UltraStudio 4K Mini SN123456, ffmpeg vrecord; in-house,'
    # settings list was split on ',' so the additional values for 'T' are stored as individual items in the list. All other items in the list will contain 'identifier=value'. 
    # If an item in the list does not contain '=' then it is append as an additional value to the key 'T' making the value into a list of values  
    settings_dict2 = {}
    for pair in sublists[1]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict2[key] = value
        else:
            settings_dict2['T'] = [settings_dict2['T'], pair]

    # As with the identifier 'T' in the last list, 'W' can hold multiple values. Items from 3rd sublist not containing '=' are appended to the key 'W' in settings_dict3
    # For example: W=10-bit, R640x480, MYUV422p10
    settings_dict3 = {}
    for pair in sublists[2][:3]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict3[key] = value
        else:
            settings_dict3['W'] = [settings_dict3['W'], pair]

    # The lasts values in the encoder setting list are for whatever reason not separated by a ','
    # For example: 'MYUV422p10 N=AJ Lawrence'
    # This statement takes the 4th item in the 3rd sublist and splits it on a space to retrieve the last value for 'W'. In the example above, 'MYUV422p10'. 
    if isinstance(settings_dict3['W'], list):
        settings_dict3['W'].append(sublists[2][3].split(' ', 1)[0])
        
    # The 4th item in the 3rd sublist, split in the conditional above, also stores the last field of encoder settings.
    # In the case of JPC_AV_05000 this is 'N=AJ Lawrence'. To separate 'N=AJ Lawrence' from 'MYUV422p10 N=AJ Lawrence', the command below is used:
    if len(sublists[2][3].split(' ', 1)) > 1:
    # if the 4th item in the 3rd sublist split on a "," then split again on a space to get the "N=AJ Lawrence" bit should be greater than 1.
        key, value = (sublists[2][3].split(' ', 1)[1]).split("=")
        # The command above takes the 2nd half of the 4th item in the 3rd sublist, and splits it on the character '=' assigning the string before '=' to key, and after '=' to value
        settings_dict3[key] = value
        # These variables are then added as a key:value pair to the dictionary settings_dict3
    else:
        logger.warning("Issue reading final fields in encoder settings...\nSome values may not be checked!")

    return settings_dict1, settings_dict2, settings_dict3

# Only execute if this file is run directly, not imported
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ffprobe_json_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    with open(file_path, 'r') as file:
        ffmpeg_data = json.load(file)
    ffmpeg_output = {}
    ffmpeg_output['format'] = ffmpeg_data['format']
    if 'ENCODER_SETTINGS' in ffmpeg_output['format']['tags']:
        encoder_settings = ffmpeg_output['format']['tags']['ENCODER_SETTINGS']
        settings_dict1, settings_dict2, settings_dict3 = parse_encoder_settings(encoder_settings)
        logger.debug(f"Encoder Settings are:\n{settings_dict1}\n{settings_dict2}\n{settings_dict3}")
        logger.warning("To check encoder settings against expected values please run ffprobe_check")
    else:
        logger.critical("No 'encoder settings' in ffprobe output")