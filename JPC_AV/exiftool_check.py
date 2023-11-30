#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from log_setup import logger
from find_config import config_path

## creates the function "parse_exiftool" which takes the argument "file_path" 
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_exiftool(file_path):
    # creates a dictionary of expected keys and values
    expected_exif_values = config_path.config_dict['exiftool_values']

    with open(file_path, 'r') as file:
    # open exiftool text file as variable "file"
        lines = file.readlines()
        # define variable 'lines' as all individual lines in file (to be parsed in next "for loop")
    
    exif_data = {}
    
    for line in lines:
    # for each line in exiftool text file
        line = line.strip()
        # strips line of blank space with python function strip()
        key, value = [x.strip() for x in line.split(":", 1)]
        #assign variable "key" to string before ":" and variable "value" to string after ":"
        exif_data[key] = value
        # value is matched to the key, in a key:value pair

    ## Explination of the loops below:
    # The loops below assign the variables "expected_key" and "expected_value" to the key:value pairs in the "expected" dictionary defined at the beginning of the function
    # the variable "actual_value" is used to define the value of the key matching the "expected_key" in the expected_exif_values dictionary (defined above)
    # if the actual_value variable and the expected_valu variable don't match, then a string stating both values is appened to a list called "differences"

    differences = []
    # Create empty list, "differences"
    for expected_key, expected_value in expected_exif_values.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in exif_data:
        # if the key in the dictionary "General"
            actual_value = exif_data[expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                differences.append(f"{expected_key}\n\tExpected: {expected_value}\n\tActual: {actual_value}\n")
                # append this string to the list "differences"

    if not differences:
    # if the list "differences" is empty, then
        logger.debug("All specified fields and values found in the Exiftool output.")
    else:
    # if the list "differences" is not empty, then
        logger.critical("Some specified Exiftool fields or values are missing or don't match:")
        for diff in differences:
            logger.critical(f'\n\t{diff}')

# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <exiftool_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
        # assigns variable "file_path" to the text file "JPCspecs_ex.txt"
        # # This part of the script is for testing purposes and it will need to change to assign file_path programatically when run on a directory or something... TBD
    parse_exiftool(file_path)
    #runs the function "parse_exiftool" on the file assigned to the variable "file_path"