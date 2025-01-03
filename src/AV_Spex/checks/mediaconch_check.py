#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import subprocess
from ..utils.log_setup import logger
from ..utils.find_config import config_path

def find_mediaconch_policy(command_config, config_path):
    """
    Find and validate the MediaConch policy file.
    
    Args:
        command_config (object): Configuration object with tool settings
        config_path (object): Configuration path object
        
    Returns:
        str or None: Full path to the policy file, or None if not found
    """
    try:
        # Get policy filename from configuration
        policy_file = command_config.command_dict['tools']['mediaconch']['mediaconch_policy']
        policy_path = os.path.join(config_path.config_dir, policy_file)

        if not os.path.exists(policy_path):
            logger.critical(f'Policy file not found: {policy_file}')
            return None

        logger.debug(f'Using MediaConch policy {policy_file}')
        return policy_path

    except KeyError as e:
        logger.critical(f'Configuration error: {e}')
        return None
    except Exception as e:
        logger.critical(f'Unexpected error finding MediaConch policy: {e}')
        return None


def run_mediaconch_command(command, input_path, output_type, output_path, policy_path):
    """
    Run MediaConch command with specified policy and input file.
    
    Args:
        command (str): Base MediaConch command
        input_path (str): Path to the input video file
        output_type (str): Output type flag (e.g., -oc for CSV)
        output_path (str): Path to save the output file
        policy_path (str): Path to the MediaConch policy file
        
    Returns:
        bool: True if command executed successfully, False otherwise
    """
    try:
        # Construct full command
        full_command = f"{command} {policy_path} \"{input_path}\" {output_type} {output_path}"
        
        logger.debug(f'Running command: {full_command}\n')
        
        # Run the command
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        
        # Check for command execution errors
        if result.returncode != 0:
            logger.error(f"MediaConch command failed: {result.stderr}")
            return False
        
        return True

    except Exception as e:
        logger.critical(f'Error running MediaConch command: {e}')
        return False


def parse_mediaconch_output(output_path):
    """
    Parse MediaConch CSV output and log policy validation results.
    
    Args:
        output_path (str): Path to the MediaConch CSV output file
        
    Returns:
        dict: Validation results with pass/fail status for each policy check
    """
    try:
        with open(output_path, 'r', newline='') as mc_file:
            reader = csv.reader(mc_file)
            mc_header = next(reader)  # Get the header row
            mc_values = next(reader)  # Get the values row

            # Create a dictionary to track validation results
            validation_results = {}
            found_failures = False

            # Zip headers and values to create key-value pairs
            for mc_field, mc_value in zip(mc_header, mc_values):
                validation_results[mc_field] = mc_value

                # Check for failures
                if mc_value == "fail":
                    if not found_failures:
                        logger.critical("MediaConch policy failed:")
                        found_failures = True
                    logger.critical(f"{mc_field}: {mc_value}")

            # Log overall validation status
            if not found_failures:
                logger.info("MediaConch policy passed\n")
            else:
                logger.debug("")  # Add empty line after mediaconch results

            return validation_results

    except FileNotFoundError:
        logger.critical(f"MediaConch output file not found: {output_path}\n")
        return {}
    except csv.Error as e:
        logger.critical(f"Error parsing MediaConch CSV: {e}")
        return {}
    except Exception as e:
        logger.critical(f"Unexpected error processing MediaConch output: {e}")
        return {}
