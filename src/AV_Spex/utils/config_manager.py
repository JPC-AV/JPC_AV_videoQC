from dataclasses import asdict
from typing import Optional, TypeVar, Type, Dict, Any
import json

T = TypeVar('T')

class ConfigManager:
    _instance = None
    _configs: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def get_config(self, config_name: str, config_class: Type[T]) -> T:
        """Get config by name, returns default if not yet set"""
        return self._configs.get(config_name, config_class())
    
    def set_config(self, config_name: str, config: Any) -> None:
        """Set config by name"""
        self._configs[config_name] = config
    
    def update_config(self, config_name: str, updates: dict) -> None:
        """Update specific fields in a config"""
        current_config = self._configs.get(config_name)
        if current_config:
            for key, value in updates.items():
                if hasattr(current_config, key):
                    setattr(current_config, key, value)
    
    def save_to_file(self, filename: str) -> None:
        """Save all configs to JSON file"""
        config_dict = {
            name: asdict(config) 
            for name, config in self._configs.items()
        }
        with open(filename, 'w') as f:
            json.dump(config_dict, f, indent=4)
    
    def load_from_file(self, filename: str) -> None:
        """Load configs from JSON file"""
        with open(filename, 'r') as f:
            config_dict = json.load(f)
            self._configs = config_dict