import os
import csv
import subprocess
from dataclasses import dataclass, asdict, field

from ..utils.log_setup import logger
from ..utils.find_config import ChecksConfig, SpexConfig
from ..utils.config_manager import ConfigManager
from ..utils import yaml_profiles


config_mgr = ConfigManager()


def format_config_value(value, indent=0, is_nested=False):
    """Format config values for display."""
    spacer = " " * indent
    
    if isinstance(value, dict):
        formatted_str = "\n" if is_nested else ""
        for k, v in value.items():
            formatted_str += f"{spacer}{k}: {format_config_value(v, indent + 2, True)}\n"
        return formatted_str
    
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
        
    if value == 'yes': return "✅"
    if value == 'no': return "❌"
    return str(value)


def print_config(config_type='all'):
    """Print config state for specified config type(s)."""
    configs = {}
    if config_type in ['all', 'checks']:
        configs['Checks Config'] = config_mgr.get_config('checks', ChecksConfig)
    if config_type in ['all', 'spex']:
        configs['Spex Config'] = config_mgr.get_config('spex', SpexConfig)
        
    for config_name, config in configs.items():
        print(f"\n{config_name}:")
        config_dict = asdict(config)
        for key, value in config_dict.items():
            print(f"{key}:")
            print(format_config_value(value, indent=2))


def resolve_config(args, config_mapping):
    return config_mapping.get(args, None)