#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import xml.etree.ElementTree as ET

from ..utils.log_setup import logger
from ..utils.find_config import config_path

def parse_mediatrace(xml_file):
    expected_mediatrace = config_path.config_dict['mediatrace']

    expected_mt_keys = expected_mediatrace.keys()

    expected_encoder_settings = []
    expected_encoder_settings = expected_mediatrace['ENCODER_SETTINGS']

    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Define the namespace
    ns = {'mt': 'https://mediaarea.net/mediatrace'}

    mediatrace_output = {}
    for mt_key in expected_mt_keys:
        # Find all 'block' elements with the name attribute matching 'SimpleTag'
        simple_tags = root.findall(".//mt:block[@name='SimpleTag']", ns)
        # Iterate through all 'block' elements name matching 'SimpleTag'
        for simple_tag in simple_tags:
            # Find the 'TagName' block with the specific mediatrace field name (key) we are looking
            tag_name_block = simple_tag.find(f".//mt:block[@name='TagName']/mt:data[.='{mt_key}']", ns)
            if tag_name_block is not None:
                # Find the corresponding 'TagString' block
                tag_string_block = simple_tag.find(f".//mt:block[@name='TagString']/mt:data", ns)
                if tag_string_block is not None:
                    mediatrace_output[mt_key] = tag_string_block.text
                    break
    
    mediatrace_differences = {}
    for expected_key, expected_value in expected_mediatrace.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_mediatrace"
        if expected_key not in mediatrace_output: 
            mediatrace_differences[expected_key] = ['metadata field not found', '']
        elif len(mediatrace_output[expected_key]) == 0:
        # count the values in the dictionary "mediatrace_output" with 'len', if the values are zero, then:
             mediatrace_differences[expected_key] =  ['no metadata value found', '']
    
    if 'ENCODER_SETTINGS' in mediatrace_output:
        # initialize variables
        encoder_settings_string = mediatrace_output['ENCODER_SETTINGS']
        # split string into list using semicolons as separators. I find reg expression confusing. For reference:
            # r: Indicates a raw string, where backslashes are treated literally (important for regular expressions).
            # \s*: Matches zero or more whitespace characters (spaces, tabs, newlines, etc.).
            # ;: Matches a semicolon character.
            # \s*: Again, matches zero or more whitespace characters.
        encoder_settings_list = re.split(r'\s*;\s*', encoder_settings_string)
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
        for expected_es_key, expected_es_value in expected_encoder_settings.items():
        # defines variables "expected_es_key" and "expected_es_value" to the dictionary "expected_mediatrace"
            if expected_es_key not in encoder_settings_dict:
                # append this string to the list "mediatrace_differences"
                mediatrace_differences[f"Encoder setting field {expected_es_key}"] = ['metadata field not found', '']
            elif set(encoder_settings_dict[expected_es_key]) != set(expected_es_value):
                # Compare as sets for order insensitivity  
                mediatrace_differences[expected_es_key] = [encoder_settings_dict[expected_es_key], expected_es_value]

    if not mediatrace_differences:
        # if the list "mediatrace_differences" is empty, then
        logger.info("All specified mediatrace fields and values found in output.\n")

    if mediatrace_differences:
        logger.critical("Some specified MediaTrace fields or values are missing or don't match:")
        for mediatrace_key, values in mediatrace_differences.items():
            actual_value, expected_value = values
            logger.critical(f"{mediatrace_key} {actual_value}")
        logger.debug(f"") # adding a space after mediatrace results if there are failures
    
    return mediatrace_differences
