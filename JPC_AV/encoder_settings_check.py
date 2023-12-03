#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging


def parse_encoder_settings(encoder_settings):
    # Splitting the settings string into key-value pairs
    settings_list = [pair.strip() for pair in encoder_settings.split(",")]

    # Creating sublists based on 'O='
    sublists = []
    current_sublist = []
    for pair in settings_list:
        if 'O=' in pair:
            if current_sublist:
                sublists.append(current_sublist)
            current_sublist = [pair]
        else:
            current_sublist.append(pair)

    # Adding the last sublist
    sublists.append(current_sublist)

    # Creating dictionaries from sublists
    settings_dict1 = {}
    for pair in sublists[0]:
        key, value = pair.split("=")
        settings_dict1[key] = value

    settings_dict2 = {}
    for pair in sublists[1]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict2[key] = value
        else:
            settings_dict2['T'] = [settings_dict2['T'], pair]

    settings_dict3 = {}
    for pair in sublists[2][:3]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict3[key] = value
        else:
            settings_dict3['W'] = [settings_dict3['W'], pair]

    if isinstance(settings_dict3['W'], list):
        settings_dict3['W'].append(sublists[2][3].split(' ', 1)[0])
        
    key, value = (sublists[2][3].split(' ', 1)[1]).split("=")
    settings_dict3[key] = value

    return settings_dict1, settings_dict2, settings_dict3

    #print(settings_dict1)
    #print(settings_dict2)
    #print(settings_dict3)

    # https://www.google.com/search?q=python+how+to+append+to+an+existing+value+in+dictionary&oq=&gs_lcrp=EgZjaHJvbWUqCQgCEEUYOxjCAzIJCAAQRRg7GMIDMgkIARBFGDsYwgMyCQgCEEUYOxjCAzIJCAMQRRg7GMIDMgkIBBBFGDsYwgMyCQgFEEUYOxjCAzIJCAYQRRg7GMIDMgkIBxBFGDsYwgPSAQo3NDI2MTNqMGo3qAIIsAIB&sourceid=chrome&ie=UTF-8#kpvalbx=_eslTZbzAMcCz0PEPpOCQ-Aw_27
    # https://www.geeksforgeeks.org/python-split-list-into-lists-by-particular-value/#

# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ffprobe_json_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    parse_encoder_settings(file_path)
    #runs the function "parse_mediainfo" on the file assigned to the variable "file_path"