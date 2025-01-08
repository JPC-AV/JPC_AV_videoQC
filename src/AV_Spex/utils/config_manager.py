from dataclasses import asdict, is_dataclass
from typing import Optional, TypeVar, Type, Dict, Any, get_type_hints
import json
import os
from pathlib import Path

from ..utils.log_setup import logger

T = TypeVar('T')

class ConfigManager:
    _instance = None
    _configs: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
            if not os.path.exists(config_dir):
                raise FileNotFoundError(f"Config directory not found at {config_dir}")
        return cls._instance
    
    @property
    def project_root(self) -> str:
        return os.path.dirname(os.path.dirname(__file__))

    def find_file(self, filename: str, subdir: str = 'config') -> Optional[str]:
        file_path = os.path.join(self.project_root, subdir, filename)
        # print(f"Looking for config file at: {file_path}")
        # print(f"Project root is: {self.project_root}")
        return file_path if os.path.exists(file_path) else None

    def _load_json_config(self, config_name: str, last_used: bool = False) -> dict:
        """
        Load JSON config file by name
        Args:
            config_name: Name of the config file
            last_used: If True, look for last_used_{config_name}_config.json first
        """
        if last_used:
            last_used_path = self.find_file(f"last_used_{config_name}_config.json")
            if last_used_path and os.path.exists(last_used_path):
                try:
                    with open(last_used_path, 'r') as f:
                        data = json.load(f)
                        logger.debug(f"Successfully loaded last_used_{config_name}_config.json")
                        return data
                except json.JSONDecodeError:
                    logger.critical(f"Error loading last used config, falling back to defaults")

        # Load default config if last_used is False or last_used config doesn't exist
        json_path = self.find_file(f"{config_name}_config.json")
        # print(f"Attempting to load config from: {json_path}")
        
        if not json_path or not os.path.exists(json_path):
            raise FileNotFoundError(
                f"Config file {config_name}_config.json not found. "
                f"Required configuration files must be present in the config directory."
            )
            
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded {config_name}_config.json")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing {config_name}_config.json: {str(e)}")


    def _create_dataclass_instance(self, cls: Type[T], data: dict) -> T:
        """
        Create a dataclass instance from a dictionary, ensuring nested structures
        are also converted to dataclasses.
        """
        if not data:
            raise ValueError(f"No data provided to create {cls.__name__} instance")

        type_hints = get_type_hints(cls)
        processed_data = {}
        
        for field_name, field_type in type_hints.items():
            if field_name not in data:
                logger.warning(f"Field {field_name} not found in data for {cls.__name__}")
                continue
                
            field_value = data[field_name]
            
            # Handle None values
            if field_value is None:
                processed_data[field_name] = None
                continue
            
            # Extract actual type from Optional
            if str(field_type).startswith('typing.Optional'):
                field_type = field_type.__args__[0]
            
            # Handle nested dataclasses
            if hasattr(field_type, '__dataclass_fields__'):
                if isinstance(field_value, dict):
                    processed_data[field_name] = self._create_dataclass_instance(
                        field_type, field_value
                    )
                else:
                    raise ValueError(
                        f"Expected dict for {field_name}, got {type(field_value)}"
                    )
                    
            # Handle List types
            elif str(field_type).startswith('typing.List'):
                if not isinstance(field_value, list):
                    raise ValueError(
                        f"Expected list for {field_name}, got {type(field_value)}"
                    )
                # Get the type of list elements
                element_type = field_type.__args__[0]
                if hasattr(element_type, '__dataclass_fields__'):
                    # Convert each list element to a dataclass if needed
                    processed_data[field_name] = [
                        self._create_dataclass_instance(element_type, item)
                        if isinstance(item, dict) else item
                        for item in field_value
                    ]
                else:
                    processed_data[field_name] = field_value
                    
            # Handle Dict types
            elif str(field_type).startswith('typing.Dict'):
                if not isinstance(field_value, dict):
                    raise ValueError(
                        f"Expected dict for {field_name}, got {type(field_value)}"
                    )
                # Get the value type of the dict
                value_type = field_type.__args__[1]
                if hasattr(value_type, '__dataclass_fields__'):
                    # Convert each dict value to a dataclass if needed
                    processed_data[field_name] = {
                        k: self._create_dataclass_instance(value_type, v)
                        if isinstance(v, dict) else v
                        for k, v in field_value.items()
                    }
                else:
                    processed_data[field_name] = field_value
            
            # Handle basic types
            else:
                processed_data[field_name] = field_value
        
        return cls(**processed_data)

    def update_config(self, config_name: str, updates: dict) -> None:
        """
        Update config while maintaining dataclass structure throughout.
        """
        current_config = self._configs.get(config_name)
        if not current_config:
            logger.error(f"No current {config_name} config found")
            return

        def update_recursively(target, source):
            for key, value in source.items():
                if not hasattr(target, key):
                    logger.error(f"Field '{key}' not found in config")
                    continue
                    
                current_value = getattr(target, key)
                
                if isinstance(value, dict):
                    if hasattr(current_value, '__dataclass_fields__'):
                        # If current value is a dataclass, update it recursively
                        update_recursively(current_value, value)
                    else:
                        # If we're updating a dict field
                        setattr(target, key, value)
                else:
                    # Update the value directly
                    setattr(target, key, value)

        # Perform the update
        update_recursively(current_config, updates)
        # logger.debug(f"Updated {config_name} config")
        
        # Save the updated config
        self.save_last_used_config(config_name)

    def get_config(self, config_name: str, config_class: Type[T]) -> T:
        """
        Get config, ensuring it's always returned as a proper dataclass instance.
        """
        if config_name not in self._configs:
            # Load default config
            default_config = self._load_json_config(config_name, last_used=False)
            
            try:
                # Try to load and merge last used config
                last_used_data = self._load_json_config(config_name, last_used=True)
                self._deep_merge_dict(default_config, last_used_data)
            except (FileNotFoundError, json.JSONDecodeError):
                logger.debug(f"No valid last used config found for {config_name}")
                
            # Create dataclass instance
            self._configs[config_name] = self._create_dataclass_instance(
                config_class, default_config
            )
            
        return self._configs[config_name]

    def _deep_merge_dict(self, target: dict, source: dict) -> None:
        """
        Recursively merge source dict into target dict while preserving types.
        """
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    self._deep_merge_dict(target[key], value)
                else:
                    target[key] = value

    def save_config(self, config_name: str) -> None:
        """Save current config state to JSON file"""
        config = self._configs.get(config_name)
        if not config:
            return
            
        json_path = self.find_file(f"{config_name}_config.json")
        if not json_path:
            json_path = os.path.join(self.project_root, 'config', f"{config_name}_config.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
        with open(json_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)

    def save_last_used_config(self, config_name: str) -> None:
        """Save current config state as last used settings"""
        config = self._configs.get(config_name)
        if not config:
            print(f"No config found for {config_name}, cannot save last used settings")
            return
            
        last_used_path = os.path.join(
            self.project_root, 
            'config', 
            f"last_used_{config_name}_config.json"
        )
        os.makedirs(os.path.dirname(last_used_path), exist_ok=True)
        
        try:
            with open(last_used_path, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            # logger.debug(f"Successfully saved last used config for {config_name} at {last_used_path}")
        except Exception as e:
            logger.critical(f"Error saving last used config for {config_name}: {str(e)}")

    def set_config(self, config_name: str, config: Any) -> None:
        """
        Set config value, ensuring it maintains proper dataclass structure.
        
        Args:
            config_name: Name of the config to set
            config: Configuration value to set. Can be either a dataclass instance
                or a dictionary that can be converted to the appropriate dataclass.
        """
        # If it's already a dataclass instance, store it directly
        if hasattr(config, '__dataclass_fields__'):
            self._configs[config_name] = config
            return
            
        # If it's a dict, try to convert it to the appropriate dataclass
        if isinstance(config, dict):
            # Get the appropriate dataclass type from existing config
            if config_name in self._configs:
                config_class = self._configs[config_name].__class__
                self._configs[config_name] = self._create_dataclass_instance(config_class, config)
            else:
                logger.error(f"Cannot determine dataclass type for {config_name}")
                return
        else:
            logger.error(f"Config must be either a dataclass instance or a dictionary, got {type(config)}")
            return
        
        # Save the updated config
        self.save_last_used_config(config_name)