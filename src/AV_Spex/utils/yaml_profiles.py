import argparse
from dataclasses import asdict, replace
from ..utils.find_config import SpexConfig, ChecksConfig
from ..utils.log_setup import logger
from ..utils.config_manager import with_checks_config


# Function to apply profile changes
@with_checks_config
def apply_profile(selected_profile, checks_config=None):
    """
    Apply profile changes to the given ChecksConfig instance.

    :param selected_profile: The profile containing updates for outputs and tools.
    :param checks_config: The ChecksConfig instance provided by the @with_checks_config decorator.
    """
    # Update outputs
    if 'outputs' in selected_profile:
        for output, output_settings in selected_profile["outputs"].items():
            if output in checks_config.outputs:
                if isinstance(output_settings, dict):
                    checks_config.outputs[output].update(output_settings)
                else:
                    checks_config.outputs[output] = output_settings

    # Update tools
    if 'tools' in selected_profile:
        for tool, updates in selected_profile["tools"].items():
            if tool in checks_config.tools:
                tool_config = checks_config.tools[tool]
                if isinstance(tool_config, dict):
                    tool_config.update(updates)
                elif hasattr(tool_config, "__dict__"):
                    for key, value in updates.items():
                        if hasattr(tool_config, key):
                            setattr(tool_config, key, value)


@with_checks_config
def apply_by_name(tool_names, checks_config=None):
    """
    Apply a profile by enabling specific tools while turning others off.

    :param tool_names: A list of tool names to enable.
    :param checks_config: The ChecksConfig instance provided by the @with_checks_config decorator.
    """
    # Turn everything off initially
    profile_all_off = {
        "tools": {tool: {"run_tool": "no", "check_tool": "no"} for tool in checks_config.tools}
    }
    apply_profile(profile_all_off, checks_config=checks_config)

    # Create a profile to enable the selected tools
    tool_profile = {"tools": {}}

    for tool in tool_names:
        # Check if the tool exists in checks_config
        if tool in checks_config.tools:
            tool_profile["tools"][tool] = {
                subfield: "yes" for subfield in checks_config.tools[tool].__dict__
            }
            logger.debug(f"{tool} set to 'on'")

    # Apply the selective changes
    apply_profile(tool_profile, checks_config=checks_config)


@with_checks_config
def toggle_on(tool_names, checks_config=None):
    """
    Enable specific tools by setting all their subfields to 'yes'.

    :param tool_names: A list of tool names to enable.
    :param checks_config: The ChecksConfig instance provided by the @with_checks_config decorator.
    """
    tool_profile = {"tools": {}}

    for tool in tool_names:
        # Check if the tool exists in checks_config
        if tool in checks_config.tools:
            tool_profile["tools"][tool] = {
                subfield: "yes" for subfield in checks_config.tools[tool].__dict__
            }
            logger.debug(f"{tool} set to 'on'")

    # Apply the changes
    apply_profile(tool_profile, checks_config=checks_config)


@with_checks_config
def toggle_off(tool_names, checks_config=None):
    """
    Disable specific tools by setting all their subfields to 'no'.

    :param tool_names: A list of tool names to disable.
    :param checks_config: The ChecksConfig instance provided by the @with_checks_config decorator.
    """
    tool_profile = {"tools": {}}

    for tool in tool_names:
        # Check if the tool exists in checks_config
        if tool in checks_config.tools:
            tool_profile["tools"][tool] = {
                subfield: "no" for subfield in checks_config.tools[tool].__dict__
            }
            logger.debug(f"{tool} set to 'off'")

    # Apply the changes
    apply_profile(tool_profile, checks_config=checks_config)


def update_config(checks_config: ChecksConfig, nested_key: str, value_dict: dict) -> ChecksConfig:
    # Convert the dataclass to a dictionary for easier manipulation
    config_dict = asdict(checks_config)

    # Split the nested key into its parts
    keys = nested_key.split('.')
    current_dict = config_dict

    # Traverse the dictionary to the desired nested level
    for key in keys[:-1]:
        if key in current_dict:
            current_dict = current_dict[key]
        else:
            logger.warning(f"Key '{key}' not found in configuration.")
            return checks_config  # Return the original config if key is not found

    last_key = keys[-1]
    if last_key in current_dict:
        # Remove keys from current_dict[last_key] that are not in value_dict
        for k in list(current_dict[last_key].keys()):
            if k not in value_dict:
                del current_dict[last_key][k]

        # Create a new ordered dictionary based on value_dict
        ordered_dict = {k: value_dict[k] for k in value_dict}

        # Replace the old dictionary with the ordered one
        current_dict[last_key].clear()
        current_dict[last_key].update(ordered_dict)

        logger.info(f"Configuration updated for key '{nested_key}'.")

    # Create a new ChecksConfig instance with updated values
    return ChecksConfig(**config_dict)


# Function to save the current state of the command_config.yaml to a dictionary (profile)
def save_current_profile(config):
    if config == command_config:
        with open(config.command_yml, 'r') as f:
            current_profile = yaml.load(f)
    else:
        with open(config.config_yml, 'r') as f:
            current_profile = yaml.load(f)
    return current_profile


# Function to save the current profile to a new YAML file
def save_profile_to_file(config, new_file_path):
    current_profile = save_current_profile(config)
    if current_profile:
        with open(new_file_path, 'w') as f:
            yaml.dump(current_profile, f)
        logger.info(f'Profile saved to {new_file_path}\n')
    else:
        logger.critical('Unable to save command profile!\n')


def apply_selected_profile(profile_name, checks_config):
    if profile_name == "step1":
        profile = profile_step1
    elif profile_name == "step2":
        profile = profile_step2
    else:
        raise ValueError(f"Unknown profile: {profile_name}")

    apply_profile(checks_config, profile)
    logger.info(f'command_config.yaml updated to match selected tool profile: {profile_name}')


def checkbox_on(checks_config: ChecksConfig, command_name: str, state: str) -> ChecksConfig:
    """
    Recursively updates the value of `command_name` in a nested dictionary
    and updates the ChecksConfig instance.

    Parameters:
        checks_config (ChecksConfig): An instance of the ChecksConfig class.
        command_name (str): The key to find and update its value.
        state (str): Either "yes" or "no". Determines the value to set.

    Returns:
        ChecksConfig: Updated ChecksConfig instance.
    """
    if state not in ["yes", "no"]:
        raise ValueError("Invalid state. Use 'yes' or 'no'.")

    new_value = state  # We're already passing 'yes' or 'no'

    def update_dict(d):
        """Helper function to recursively update the dictionary."""
        updated = False
        for key, value in d.items():
            if isinstance(value, dict):  # If the value is a dictionary, recurse into it.
                if update_dict(value):
                    updated = True
            elif key == command_name:  # If the key matches, update the value.
                if d[key] != new_value:  # Only update if value is different
                    d[key] = new_value
                    logger.info(f"{command_name} set to '{state}'")
                    updated = True
        return updated

    # Convert the dataclass to a dictionary for manipulation
    config_dict = asdict(checks_config)

    # Update the dictionary
    if update_dict(config_dict):
        # Create a new ChecksConfig instance with updated values
        return ChecksConfig(**config_dict)
    
    return checks_config  # Return original if no updates were made


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
            "check_ffprobe": 'no',
            "run_ffprobe": 'yes'
        },
        "mediaconch": {
            "run_mediaconch": 'yes'
        },
        "mediainfo": {
            "check_mediainfo": 'yes',
            "run_mediainfo": 'yes'
        },
        "mediatrace": {
            "check_mediatrace": 'yes',
            "run_mediatrace": 'yes'
        },
    },
    "outputs": {
        "report": 'no',
        "access_file": 'no',
        "fixity": {
            "output_fixity": 'yes',
            "check_fixity": 'no',
            "embed_stream_fixity": 'yes',
            "validate_stream_fixity": 'no'
        }
    }
}

profile_step2 = {
    "tools": {
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
        "mediatrace": {
            "check_mediatrace": 'yes',
            "run_mediatrace": 'no'
        },
        "mediainfo": {
            "check_mediainfo": 'yes',
            "run_mediainfo": 'no'
        },
        "qctools": {
            "run_qctools": 'yes',
            "check_qctools": 'yes'
        },
        "qct-parse": {
            "barsDetection": True,
            "evaluateBars": True,
            "contentFilter": None,
            "profile": None,
            "thumbExport": True
        }
    },
    "outputs": {
        "report": 'yes',
        "access_file": 'no',
        "fixity": {
            "output_fixity": 'no',
            "check_fixity": 'yes',
            "embed_stream_fixity": 'no',
            "validate_stream_fixity": 'yes'
        }
    }
}

profile_allOff = {
    "tools": {
        "exiftool": {
            "check_exiftool": 'no',
            "run_exiftool": 'no'
        },
        "ffprobe": {
            "check_ffprobe": 'no',
            "run_ffprobe": 'no'
        },
        "mediaconch": {
            "run_mediaconch": 'no'
        },
        "mediatrace": {
            "check_mediatrace": 'no',
            "run_mediatrace": 'no'
        },
        "mediainfo": {
            "check_mediainfo": 'no',
            "run_mediainfo": 'no'
        },
        "qctools": {
            "run_qctools": 'no',
            "check_qctools": 'no'
        },
        "qct-parse": {
            "barsDetection": None,
            "evaluateBars": None,
            "contentFilter": None,
            "profile": None,
            "thumbExport": None
        }
    },
    "outputs": {
        "report": 'no',
        "access_file": 'no',
        "fixity": {
            "output_fixity": 'no',
            "check_fixity": 'no',
            "embed_stream_fixity": 'no',
            "validate_stream_fixity": 'no'
        }
    }
}

JPC_AV_SVHS = {
    "Source VTR": ["SVO5800", "SN 122345", "composite", "analog balanced"], 
    "TBC/Framesync": ["DPS575 with flash firmware h2.16", "SN 15230", "SDI", "audio embedded"], 
    "ADC": ["DPS575 with flash firmware h2.16", "SN 15230", "SDI"], 
    "Capture Device": ["Black Magic Ultra Jam", "SN B022159", "Thunderbolt"],
    "Computer": ["2023 Mac Mini", "Apple M2 Pro chip", "SN H9HDW53JMV", "OS 14.5", "vrecord v2023-08-07", "ffmpeg"]
}

BVH3100 = {
    "Source VTR": ["Sony BVH3100", "SN 10525", "composite", "analog balanced"],
    "TBC/Framesync": ["Sony BVH3100", "SN 10525", "composite", "analog balanced"],
    "ADC": ["Leitch DPS575 with flash firmware h2.16", "SN 15230", "SDI", "embedded"],
    "Capture Device": ["Blackmagic Design UltraStudio 4K Extreme", "SN B022159", "Thunderbolt"],
    "Computer": ["2023 Mac Mini", "Apple M2 Pro chip", "SN H9HDW53JMV", "OS 14.5", "vrecord v2023-08-07", "ffmpeg"]
}

bowser_filename = {
    "Collection": "2012_79",
    "MediaType": "2",
    "ObjectID": r"\d{3}_\d{1}[a-zA-Z]",
    "DigitalGeneration": "PM",
    "FileExtension": "mkv"
}

JPCAV_filename = {
    "Collection": "JPC",
    "MediaType": "AV",
    "ObjectID": r"\d{5}",
    "FileExtension": "mkv"
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
