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
            # Debug print at initialization
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
            print(f"Config directory: {config_dir}")
            if os.path.exists(config_dir):
                print(f"Files in config directory: {os.listdir(config_dir)}")
            else:
                raise FileNotFoundError(f"Config directory not found at {config_dir}")
        return cls._instance

    @property
    def project_root(self) -> str:
        """Get AV_Spex module directory"""
        return os.path.dirname(os.path.dirname(__file__))  # Go up two levels: utils -> AV_Spex

    def find_file(self, filename: str, subdir: str = 'config') -> Optional[str]:
        """Find file in project directory structure"""
        file_path = os.path.join(self.project_root, subdir, filename)
        print(f"Looking for config file at: {file_path}")
        print(f"Project root is: {self.project_root}")
        return file_path if os.path.exists(file_path) else None

    def _load_json_config(self, config_name: str) -> dict:
        """Load JSON config file by name"""
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

        # Get type hints for the dataclass
        type_hints = get_type_hints(cls)
        
        # Process each field according to its type
        processed_data = {}
        for field_name, field_value in data.items():
            if field_name not in type_hints:
                continue
                
            field_type = type_hints[field_name]
            
            # Handle nested dataclasses
            if (isinstance(field_value, dict) and 
                hasattr(field_type, '__dataclass_fields__')):
                processed_data[field_name] = self._create_dataclass_instance(
                    field_type, field_value
                )
            # Handle dict fields
            elif (isinstance(field_value, dict) and 
                  str(field_type).startswith('typing.Dict')):
                processed_data[field_name] = field_value
            # Handle list fields that might contain dataclasses
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
        """Get config by name, load from JSON if not exists"""
        if config_name not in self._configs:
            # Load from JSON - will raise error if not found
            json_data = self._load_json_config(config_name)
            self._configs[config_name] = self._create_dataclass_instance(
                config_class, json_data
            )
                
        return self._configs[config_name]

    def set_config(self, config_name: str, config: Any) -> None:
        """Set config by name"""
        self._configs[config_name] = config

    def update_config(self, config_name: str, updates: dict) -> None:
        """Update config recursively"""
        def update_recursively(target, source):
            for key, value in source.items():
                if isinstance(value, dict):
                    if not hasattr(target, key):
                        continue
                    current = getattr(target, key)
                    if isinstance(current, dict):
                        current.update(value)
                    else:
                        for subkey, subvalue in value.items():
                            if hasattr(current, subkey):
                                setattr(current, subkey, subvalue)
                elif hasattr(target, key):
                    setattr(target, key, value)

        current_config = self._configs.get(config_name)
        if current_config:
            update_recursively(current_config, updates)

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