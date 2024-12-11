import argparse
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from ..utils.find_config import config_path, command_config, yaml
from ..utils.log_setup import logger


# Function to apply profile changes
def apply_profile(command_config, selected_profile):
    with open(command_config.command_yml, "r") as f:
        command_dict = yaml.load(f)

    if 'outputs' in selected_profile:
        for output, output_settings in selected_profile["outputs"].items():
            if output in command_dict["outputs"]:
                if isinstance(output_settings, dict):
                    command_dict["outputs"][output].update(output_settings)
                else:
                    command_dict["outputs"][output] = output_settings

    if 'tools' in selected_profile:
        for tool, updates in selected_profile["tools"].items():
            if tool in command_dict["tools"]:
                command_dict["tools"][tool].update(updates)

    with open(command_config.command_yml, "w") as f:
        yaml.dump(command_dict, f)


def apply_by_name(command_config, tool_names):
    apply_profile(command_config, profile_allOff)  # Turn everything off initially

    tool_profile = {"tools": {}}  # Initialize the tool_profile dictionary

    for tool in tool_names:
        # Check if the tool exists in the command_config
        if tool in command_config.command_dict["tools"]:
            tool_profile["tools"][tool] = {
                subfield: "yes" for subfield in command_config.command_dict["tools"][tool]
            }
            logger.debug(f"{tool} set to 'on'")

    apply_profile(command_config, tool_profile)  # Apply the selective changes


def toggle_on(command_config, tool_names):

    tool_profile = {"tools": {}}  # Initialize the tool_profile dictionary

    for tool in tool_names:
        # Check if the tool exists in the command_config
        if tool in command_config.command_dict["tools"]:
            tool_profile["tools"][tool] = {
                subfield: "yes" for subfield in command_config.command_dict["tools"][tool]
            }
            logger.debug(f"{tool} set to 'on'")

    apply_profile(command_config, tool_profile)  # Apply the selective changes


def toggle_off(command_config, tool_names):

    tool_profile = {"tools": {}}  # Initialize the tool_profile dictionary

    for tool in tool_names:
        # Check if the tool exists in the command_config
        if tool in command_config.command_dict["tools"]:
            tool_profile["tools"][tool] = {
                subfield: "no" for subfield in command_config.command_dict["tools"][tool]
            }
            logger.debug(f"{tool} set to 'off'")

    apply_profile(command_config, tool_profile)  # Apply the selective changes


def update_config(config_path, nested_key, value_dict):
    with open(config_path.config_yml, "r") as f:
        config_dict = yaml.load(f)

    keys = nested_key.split('.')                # creates a list of keys from the input, for example 'ffmpeg_values.format.tags.ENCODER_SETTINGS'
    current_dict = config_dict                  # initializes current_dict as config.yaml, this var will be reset in the for loop below
    for key in keys[:-1]:                       # Iterating through the keys (except the last one)
        if key in current_dict:             
            current_dict = current_dict[key]
        else:
            return                              # If the current key is in the current_dict, move loop "in" to nested dict
    last_key = keys[-1]
    # The code block above should get us to the nested dictionary we want to update 
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

        with open(config_path.config_yml, 'w') as y:
            yaml.dump(config_dict, y)
            logger.info(f'config.yaml updated to match profile {last_key}\n')


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


def apply_selected_profile(profile_name, command_config):
    if profile_name == "step1":
        profile = profile_step1
    elif profile_name == "step2":
        profile = profile_step2
    else:
        raise ValueError(f"Unknown profile: {profile_name}")

    apply_profile(command_config, profile)
    logger.info(f'command_config.yaml updated to match selected tool profile: {profile_name}')

def checkbox_on(command_config, command_name, state):
    """
    Recursively updates the value of `command_name` in a nested dictionary
    and saves the updated dictionary back to the YAML file.

    Parameters:
        command_config (CommandConfig): An instance of the CommandConfig class.
        command_name (str): The key to find and update its value.
        state (str): Either "on" or "off". Determines the value to set.
    """
    if state not in ["on", "off"]:
        raise ValueError("Invalid state. Use 'on' or 'off'.")
    
    new_value = 'yes' if state == 'on' else 'no'

    def update_dict(d):
        """Helper function to recursively update the dictionary."""
        for key, value in d.items():
            if isinstance(value, dict):  # If the value is a dictionary, recurse into it.
                update_dict(value)
            elif key == command_name:  # If the key matches, update the value.
                d[key] = new_value
                logger.info(f"{command_name} set to '{state}'")  # Use logging if needed.

    # Update the command_dict
    update_dict(command_config.command_dict)

    # Save the updated dictionary back to the YAML file
    with open(command_config.command_yml, 'w') as f:
        yaml.dump(command_config.command_dict, f)


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
            "check_stream_fixity": 'no'
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
            "check_stream_fixity": 'yes'
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
            "check_stream_fixity": 'no'
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
