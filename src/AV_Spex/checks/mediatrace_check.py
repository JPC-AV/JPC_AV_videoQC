#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import subprocess
import xml.etree.ElementTree as ET

from ..utils.log_setup import logger
from ..utils.find_config import config_path

def parse_mediatrace(xml_file):
    expected_mediatrace = config_path.config_dict['mediatrace']
    expected_mt_keys = expected_mediatrace.keys()

    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Define the namespace
    ns = {'mt': 'https://mediaarea.net/mediatrace'}

    mediatrace_output = {}
    for mt_key in expected_mt_keys:
    
        # Find all 'block' elements with the name attribute matching 'SimpleTag'
        simple_tags = root.findall(".//mt:block[@name='SimpleTag']", ns)

        for simple_tag in simple_tags:
            # Find the 'TagName' block with the specific string_we_have
            tag_name_block = simple_tag.find(f".//mt:block[@name='TagName']/mt:data[.='{mt_key}']", ns)
            if tag_name_block is not None:
                # Find the corresponding 'TagString' block
                tag_string_block = simple_tag.find(f".//mt:block[@name='TagString']/mt:data", ns)
                if tag_string_block is not None:
                    mediatrace_output[mt_key] = tag_string_block.text
                    #found = True
                    break
        #if not found:
         #       mediatrace_output[mt_key] = None
    
    mediatrace_differences = []
    for expected_key, expected_value in expected_mediatrace.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_mediatrace"
        if expected_key not in mediatrace_output:
            mediatrace_differences.append(f"MediaTrace metadata field {expected_key} does not exist") 
        elif len(mediatrace_output[expected_key]) == 0:
        # count the values in the dictionary "mediatrace_output" with 'len', if the values are zero, then:
            mediatrace_differences.append(f"MediaTrace: {expected_key} is empty")
            # append this string to the list "mediatrace_differences"

    if not mediatrace_differences:
        # if the list "mediatrace_differences" is empty, then
        logger.info("\nAll specified mediatrace fields and values found in  output.")

    if mediatrace_differences:
        logger.critical("\nSome specified MediaTrace fields or values are missing or don't match:")
        for diff in mediatrace_differences:
            logger.critical(f"{diff}")
