from dataclasses import asdict
from typing import Optional, TypeVar, Type, Dict, Any
import json
import os

T = TypeVar('T')

class ConfigManager:
    _instance = None
    _configs: Dict[str, Any] = {}
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    def find_file(self, filename: str, subdir: str = 'config') -> str:
        """Find file in project directory structure"""
        file_path = os.path.join(self.project_root, subdir, filename)
        return file_path if os.path.exists(file_path) else None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def get_config(self, config_name: str, config_class: Type[T]) -> T:
        """Get config by name, creates new if not exists"""
        if config_name not in self._configs:
            self._configs[config_name] = config_class()
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
                        # Handle mediaconch special case
                        if key == "mediaconch":
                            current.update(value)
                    else:
                        # Handle dataclass attributes
                        for subkey, subvalue in value.items():
                            if hasattr(current, subkey):
                                setattr(current, subkey, subvalue)
                elif hasattr(target, key):
                    setattr(target, key, value)

        current_config = self._configs.get(config_name)
        if current_config:
            update_recursively(current_config, updates)