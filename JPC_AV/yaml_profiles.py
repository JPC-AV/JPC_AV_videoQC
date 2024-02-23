import os
import sys
import yaml
import argparse
from find_config import config_path, command_config
from log_setup import logger, console_handler

# Function to apply profile changes
def apply_profile(command_config, selected_profile):
    for output, output_settings in selected_profile["outputs"].items():
        if output == "difference_csv":
            command_config.command_dict["outputs"][output] = output_settings  # Assign the value directly
        elif output == "access_file":
            command_config.command_dict["outputs"][output] = output_settings  # Assign the value directly
        elif output in command_config.command_dict["outputs"]:
            if isinstance(output_settings, dict):
                if output in command_config.command_dict["outputs"]:
                    command_config.command_dict["outputs"][output].update(output_settings)
    for tool, updates in selected_profile["tools"].items():
        if tool in command_config.command_dict["tools"]:
            command_config.command_dict["tools"][tool].update(updates)
    
    # Optionally, write back to the YAML file
    with open(command_config.command_yml, "w") as f:
        f.write("---\n")
        yaml.safe_dump(command_config.command_dict, f)
        logger.info(f'command_config.yaml updated')

profile_step1 = {
    "tools": {
        "qctools": {
            "run_qctools": 'no',
            "check_qctools": 'no'   
        },
        "exiftool": {
            "check_exiftool": 'yes',
            "run_exiftool": 'yes'
        },
        "ffprobe": {
            "check_ffprobe": 'yes',
            "run_ffprobe": 'yes'
        },
        "mediaconch": {
            "run_mediaconch": 'yes'
        },
        "mediainfo": {
            "check_mediainfo": 'yes',
            "run_mediainfo": 'yes'
        }
    },
    "outputs": {
        "difference_csv": 'yes',
        "access_file": 'yes',
        "fixity": {
            "output_fixity": 'yes',
            "check_fixity": 'no',
            "embed_stream_fixity": 'yes',
            "check_stream_fixity": 'no'
        }
    }
}

profile_step2 = {
    "tools": {
        "qctools": {
            "run_qctools": 'yes',
            "check_qctools": 'no'
        },
        "exiftool": {
            "check_exiftool": 'yes',
            "run_exiftool": 'no'
        },
        "ffprobe": {
            "check_ffprobe": 'yes',
            "run_ffprobe": 'no'
        },
        "mediaconch": {
            "run_mediaconch": 'yes'
        },
        "mediainfo": {
            "check_mediainfo": 'yes',
            "run_mediainfo": 'no'
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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Change command_config.yaml to processing profile")
    parser.add_argument("--profile", choices=["step1", "step2"], help="Select processing profile (step1 or step2)")

    args = parser.parse_args()

    selected_profile = None
    if args.profile:
        if args.profile == "step1":
            selected_profile = profile_step1
        elif args.profile == "step2":
            selected_profile = profile_step2

    return selected_profile

# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    selected_profile = parse_arguments()
    apply_profile(command_config, selected_profile)


