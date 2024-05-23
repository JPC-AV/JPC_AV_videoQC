import os
from ruamel.yaml import YAML
from ..utils.log_setup import logger

yaml = YAML()
yaml.preserve_quotes = True

class ConfigPath:
    def __init__(self):
        # Get the absolute path of the script file
        script_path = os.path.dirname(os.path.abspath(__file__))

        # Extract the directory containing the script file
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
        self.config_dir = os.path.join(self.root_dir, 'config')
        self.config_yml = os.path.join(self.config_dir, 'config.yaml')

        # logger.debug(f'config.yaml sourced from {self.config_yml}')
        
        with open(self.config_yml) as f:
            self.config_dict = yaml.load(f)

class CommandConfig:
    def __init__(self):
        # Get the absolute path of the script file
        script_path = os.path.dirname(os.path.abspath(__file__))

        # Extract the directory containing the script file
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
        self.config_dir = os.path.join(self.root_dir, 'config')
        self.command_yml = os.path.join(self.config_dir, 'command_config.yaml')

        # logger.debug(f'command_config.yaml sourced from {self.command_yml}')
        
        with open(self.command_yml) as f:
            self.command_dict = yaml.load(f)

# Create an instance of the ConfigPath class
config_path = ConfigPath()

# Create an instance of the CommandConfig class
command_config = CommandConfig()
