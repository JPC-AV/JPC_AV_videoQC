from dataclasses import asdict, is_dataclass
from typing import Optional, TypeVar, Type, Dict, Any, get_type_hints
import json
import os
from pathlib import Path

T = TypeVar('T')

class ConfigManager:
    _instance = None
    _configs: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
            print(f"Config directory: {config_dir}")
            if os.path.exists(config_dir):
                print(f"Files in config directory: {os.listdir(config_dir)}")
            else:
                raise FileNotFoundError(f"Config directory not found at {config_dir}")
        return cls._instance

    @property
    def project_root(self) -> str:
        return os.path.dirname(os.path.dirname(__file__))

    def find_file(self, filename: str, subdir: str = 'config') -> Optional[str]:
        file_path = os.path.join(self.project_root, subdir, filename)
        print(f"Looking for config file at: {file_path}")
        print(f"Project root is: {self.project_root}")
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
                        print(f"Successfully loaded last_used_{config_name}_config.json")
                        return data
                except json.JSONDecodeError:
                    print(f"Error loading last used config, falling back to defaults")

        # Load default config if last_used is False or last_used config doesn't exist
        json_path = self.find_file(f"{config_name}_config.json")
        print(f"Attempting to load config from: {json_path}")
        
        if not json_path or not os.path.exists(json_path):
            raise FileNotFoundError(
                f"Config file {config_name}_config.json not found. "
                f"Required configuration files must be present in the config directory."
            )
            
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                print(f"Successfully loaded {config_name}_config.json")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing {config_name}_config.json: {str(e)}")

    def _create_dataclass_instance(self, cls: Type[T], data: dict) -> T:
        """Recursively create dataclass instances from dict data"""
        if not data:
            raise ValueError(f"No data provided to create {cls.__name__} instance")

        type_hints = get_type_hints(cls)
        processed_data = {}
        for field_name, field_value in data.items():
            if field_name not in type_hints:
                continue
                
            field_type = type_hints[field_name]
            
            if (isinstance(field_value, dict) and 
                hasattr(field_type, '__dataclass_fields__')):
                processed_data[field_name] = self._create_dataclass_instance(
                    field_type, field_value
                )
            elif (isinstance(field_value, dict) and 
                  str(field_type).startswith('typing.Dict')):
                processed_data[field_name] = field_value
            elif (isinstance(field_value, list) and 
                  str(field_type).startswith('typing.List')):
                processed_data[field_name] = [
                    self._create_dataclass_instance(v.__class__, v) 
                    if is_dataclass(v) else v
                    for v in field_value
                ]
            else:
                processed_data[field_name] = field_value
                
        return cls(**processed_data)

    def get_config(self, config_name: str, config_class: Type[T]) -> T:
        """Get config by name, trying last used settings first"""
        if config_name not in self._configs:
            # Try to load last used config first
            try:
                json_data = self._load_json_config(config_name, last_used=True)
                print(f"Successfully loaded last used config for {config_name}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # If last used config doesn't exist or is invalid, load default config
                print(f"No valid last used config found for {config_name}, loading defaults")
                json_data = self._load_json_config(config_name, last_used=False)
                # Create a last used config from the defaults
                self._configs[config_name] = self._create_dataclass_instance(
                    config_class, json_data
                )
                self.save_last_used_config(config_name)
                return self._configs[config_name]
            
            self._configs[config_name] = self._create_dataclass_instance(
                config_class, json_data
            )
                
        return self._configs[config_name]

    def set_config(self, config_name: str, config: Any) -> None:
        self._configs[config_name] = config

    def update_config(self, config_name: str, updates: dict) -> None:
        """Update config and save as last used"""
        print(f"Updating config for {config_name}")
        print(f"Update contents: {updates}")
        
        def update_recursively(target, source):
            for key, value in source.items():
                if isinstance(value, dict):
                    if not hasattr(target, key):
                        print(f"Warning: {key} not found in target")
                        continue
                    current = getattr(target, key)
                    if isinstance(current, dict):
                        current.update(value)
                    else:
                        for subkey, subvalue in value.items():
                            if hasattr(current, subkey):
                                setattr(current, subkey, subvalue)
                                print(f"Updated {key}.{subkey} to {subvalue}")
                            else:
                                print(f"Warning: {key}.{subkey} not found in target")
                elif hasattr(target, key):
                    setattr(target, key, value)
                    print(f"Updated {key} to {value}")
                else:
                    print(f"Warning: {key} not found in target")

        current_config = self._configs.get(config_name)
        if current_config:
            update_recursively(current_config, updates)
            print(f"Saving updated config as last used for {config_name}")
            self.save_last_used_config(config_name)
        else:
            print(f"No current config found for {config_name}")

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
            print(f"Successfully saved last used config for {config_name} at {last_used_path}")
        except Exception as e:
            print(f"Error saving last used config for {config_name}: {str(e)}")