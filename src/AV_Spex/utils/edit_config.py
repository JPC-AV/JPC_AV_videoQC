import os
import csv
import subprocess
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config
from ..utils import yaml_profiles

def format_config_value(value, indent=0, is_nested=False):
    """
    Recursively formats dictionaries and lists for better presentation.
    """
    spacer = " " * indent
    formatted_str = ""

    if isinstance(value, dict):
        # Only add a newline before nested dictionaries, not for top-level keys
        if is_nested:
            formatted_str += "\n"
        for nested_key, nested_value in value.items():
            formatted_str += f"{spacer}{nested_key}: {format_config_value(nested_value, indent + 2, is_nested=True)}\n"
        return formatted_str
    elif isinstance(value, list):
        # Join list elements with commas, no brackets
        formatted_str = f"{', '.join(str(item) for item in value)}"
        return formatted_str
    elif value == 'yes':
        return "✅"  # Inline formatting for 'yes'
    elif value == 'no':
        return "❌"  # Inline formatting for 'no'
    else:
        # Handle non-dictionary, non-list values directly
        return f"{value}"
    
    
def update_yaml_configs(selected_profile, tool_names, tools_on_names, tools_off_names, 
                        sn_config_changes, fn_config_changes, save_config_type, 
                        user_profile_config):
    """Updates YAML configuration files based on provided parameters."""
    if selected_profile:
        yaml_profiles.apply_profile(command_config, selected_profile)
        logger.info(f'command_config.yaml updated to match selected tool profile\n')

    if tool_names:
        yaml_profiles.apply_by_name(command_config, tool_names)

    if tools_on_names:
        yaml_profiles.toggle_on(command_config, tools_on_names)

    if tools_off_names:
        yaml_profiles.toggle_off(command_config, tools_off_names)

    if sn_config_changes:
        yaml_profiles.update_config(config_path, 'ffmpeg_values.format.tags.ENCODER_SETTINGS', sn_config_changes)
        yaml_profiles.update_config(config_path, 'mediatrace.ENCODER_SETTINGS', sn_config_changes)

    if fn_config_changes:
        yaml_profiles.update_config(config_path, 'filename_values', fn_config_changes)

    if save_config_type:
        yaml_profiles.save_profile_to_file(save_config_type, user_profile_config)


def print_config(print_config_profile):
    """Prints the current configuration if requested."""
    if print_config_profile:
        logger.debug("The current config profile settings are:\n")
        command_config.reload()
        for key, value in command_config.command_dict.items():
            logger.warning(f"{key}:")
            logger.info(f"{format_config_value(value, indent=2)}")


def resolve_config(args, config_mapping):
    return config_mapping.get(args, None)