#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import logging
from log_setup import logger

class ConfigPath:
    def __init__(self):
        self.root_dir = os.path.join(os.path.dirname(os.path.abspath(os.getcwd())))
        self.config_dir = os.path.join(self.root_dir, 'config')
        self.config_yml = os.path.join(self.config_dir, 'config.yaml')
        logger.debug(f'config.yaml sourced from {self.config_yml}')
        with open(self.config_yml) as f:
            self.config_dict = yaml.safe_load(f)

# Create an instance of the ConfigVariables class
config_path = ConfigPath()