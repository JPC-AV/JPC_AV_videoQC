import os
import sys
import yaml
import argparse
from find_config import config_path, command_config
from log_setup import logger, console_handler

# Function to apply profile changes
def apply_profile(config, profile_name):
    profiles = {
        "Step 1": {
            "tools": {
                "qctools": {
                    "run_qctools": 'yes',
                    "check_qctools": 'no'
                }
            },
            "outputs": {
                "difference_csv": 'yes',
                "fixity": {
                    "output_fixity": 'yes',
                    "check_fixity": 'no',
                    "embed_stream_fixity": 'yes',
                    "check_stream_fixity": 'no'
                }
            }
        },
        "Step 2": {
            "tools": {
                "qctools": {
                    "run_qctools": 'no',
                    "check_qctools": 'no'
                }
            },
            "outputs": {
                "difference_csv": 'no',
                "fixity": {
                    "output_fixity": 'no',
                    "check_fixity": 'yes',
                    "embed_stream_fixity": 'no',
                    "check_stream_fixity": 'yes'
                }
            }
        }
    }

    if profile_name in profiles:
        profile = profiles[profile_name]
        for section, settings in profile.items():
            if section in config:
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        config[section][key] = value
                else:
                    config[section] = settings

    # Optionally, write back to the YAML file
    with open(command_config.command_yml, "w") as f:
        yaml.safe_dump(command_config.command_dict, f)
        logger.info(f'command_config.yaml updated to {profile_name}')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Change command_config.yaml to processing profile")
    parser.add_argument("--profile", choices=["step1", "step2"], help="Select processing profile (step1 or step2)")

    args = parser.parse_args()

    selected_profile = None
    if args.profile:
        if args.profile == "step1":
            selected_profile = "Step 1"
        elif args.profile == "step2":
            selected_profile = "Step 2"

    return selected_profile

# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    selected_profile = parse_arguments()
    apply_profile(command_config.command_dict, selected_profile)


