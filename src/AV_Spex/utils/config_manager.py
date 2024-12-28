# config_manager.py
from dataclasses import dataclass, field
from typing import Dict, Union
from functools import wraps

class ConfigManager:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config):
        """Initialize the configuration singleton with a config instance"""
        if cls._config is None:
            cls._config = config

    @classmethod
    def get_config(cls):
        """Get the current configuration instance"""
        if cls._config is None:
            raise RuntimeError("Configuration has not been initialized")
        return cls._config

    @classmethod
    def update_config(cls, path: str, value: str):
        """
        Update a configuration value using a dot-notation path
        Example: update_config("tools.ffprobe.run_tool", "yes")
        """
        if cls._config is None:
            raise RuntimeError("Configuration has not been initialized")

        def set_nested_attr(obj, path, value):
            parts = path.split('.')
            for i, part in enumerate(parts[:-1]):
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                elif isinstance(obj, dict):
                    obj = obj[part]
                else:
                    raise AttributeError(f"Invalid path: {path}")
            
            last_part = parts[-1]
            if hasattr(obj, last_part):
                setattr(obj, last_part, value)
            elif isinstance(obj, dict):
                if isinstance(obj[last_part], dict):
                    obj[last_part] = value
                else:
                    # Handle ToolCheckConfig objects
                    if hasattr(obj[last_part], '__dict__'):
                        setattr(obj[last_part], 'run_tool', value)
                    else:
                        obj[last_part] = value

        set_nested_attr(cls._config, path, value)

# Decorator for functions that need config access
def with_checks_config(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = ConfigManager.get_config()
        return func(*args, config=config, **kwargs)
    return wrapper
