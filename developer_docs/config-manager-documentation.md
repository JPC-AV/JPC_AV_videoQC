# ConfigManager Documentation

## Instantiation

The ConfigManager class uses the __new__ initialization method with the super() function to ensure only one instance is ever created:

```python
class ConfigManager:
    _instance = None  # Class-level variable to hold single instance
    _configs: Dict[str, Any] = {}  # Shared configuration cache dictionary
    
    # The __new__(cls) insures only one instance is ever created
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # One-time initialization of paths and directories
```

`super()` is used to call methods from a parent/base class. In Python, all classes ultimately inherit from `object`, which provides the basic `__new__()` implementation.

Here's the sequence:

When `super().__new__(cls)` is called:

1. `super()` gets the parent class (which is `object` in this case)
2. It calls the parent's `__new__()` method
3. It passes `cls` (`ConfigManager`) as the argument
4. The parent `object.__new__(cls)` creates a bare instance of `ConfigManager`

## The Merge Process

The ConfigManager class uses a deep merge strategy when loading the Checks config and the Spex config to combine default settings with user-specific last-used settings.

### Loading Sequence

1. When `get_config()` is called for a config that isn't in cache:
   - First loads the default configuration from the bundled configs
   - Then attempts to load and merge any last-used settings from the user config directory
   - Creates a dataclass instance from the merged result

### Deep Merge (Recursive) 

The `_deep_merge_dict()` method implements a recursive dictionary merging strategy:

```python
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
```

This function:
- Traverses both dictionaries recursively
- For nested dictionaries, continues merging deeper
- For non-dictionary values, the source value overwrites the target value
- Preserves keys in the target that don't exist in the source

### Merge Behavior Examples

```python
# Default config
default = {
    'filename_values': {
        'fn_sections': {
            'section1': {'value': 'default1'},
            'section2': {'value': 'default2'}
        },
        'FileExtension': 'mkv'
    }
}

# Last used config
last_used = {
    'filename_values': {
        'fn_sections': {
            'section1': {'value': 'custom1'}
        }
    }
}

# After merge
result = {
    'filename_values': {
        'fn_sections': {
            'section1': {'value': 'custom1'},  # Overwritten by last_used
            'section2': {'value': 'default2'}  # Preserved from default
        },
        'FileExtension': 'mkv'  # Preserved from default
    }
}
```

### Preservation of Default Values

The merge strategy preserves all keys from the default configuration. This means:
- Default settings act as a fallback for missing values
- The complete configuration structure is maintained
- New settings added to defaults will be available in user configs

### Implications

For nested dictionaries like `fn_sections`:
- Entries in the default config remain unless explicitly overwritten
- Cannot remove entries by omitting them from the last-used config
- To completely replace a collection, must implement special handling

## Config Setup

As described in the previous section, any time `config_mgr = ConfigManager()` is called would instantiate the config, but the `_instance` clause of the `ConfigManager` class prevents more than one instance of the config existing at once.

After this initial instantiation, all other `ConfigManager` instantiations will receive the same singleton instance.

The first call of `get_config()` similarly creates an instance of the Checks config or the Spex config if one is not already in the cache dictionary `_configs`.  

```python
config_mgr = ConfigManager()
checks_config = config_mgr.get_config('checks', ChecksConfig)
spex_config = config_mgr.get_config('spex', SpexConfig)
```

This calls the `ConfigManager`'s `get_config()` function, with the dataclass defined in `config_setup.py` passed as an argument:

```python
def get_config(self, config_name: str, config_class: Type[T]) -> T:
    """
    Get config, ensuring it's always returned as a proper dataclass instance.
    """
    if config_name not in self._configs:
        # Load default config first
        default_config = self._load_json_config(config_name, last_used=False)
        
        # Only try to load and merge last used config if it exists
        last_used_path = self.find_file(
            f"last_used_{config_name}_config.json",
            user_config=True
        )
        if last_used_path and os.path.exists(last_used_path):
            try:
                last_used_data = self._load_json_config(config_name, last_used=True)
                self._deep_merge_dict(default_config, last_used_data)
            except (FileNotFoundError, json.JSONDecodeError):
                logger.debug(f"No valid last used config found for {config_name}")
            
        # Create dataclass instance
        self._configs[config_name] = self._create_dataclass_instance(
            config_class, # will be either SpexConfig or ChecksConfig
            default_config
        )
        
    return self._configs[config_name]
```

The `_create_dataclass_instance()` helper function performs a recursive conversion of the JSON data into a proper dataclass instance, handling nested dataclasses, lists, and dictionaries:

```python
def _create_dataclass_instance(self, cls: Type[T], data: dict) -> T:
    # Get expected types from dataclass
    type_hints = get_type_hints(cls)  # Gets QCTParseToolConfig's type hints
    
    for field_name, field_type in type_hints.items():
        field_value = data[field_name]
        
        # Handle Optional fields (like tagname: Optional[str])
        if str(field_type).startswith('typing.Optional'):
            if field_value is None:  # JSON null becomes Python None
                processed_data[field_name] = None
                continue
            field_type = field_type.__args__[0]  # Get the inner type (str)
            
        # Handle Lists (like contentFilter: List[str])
        elif str(field_type).startswith('typing.List'):
            if not isinstance(field_value, list):
                raise ValueError(f"Expected list for {field_name}, got {type(field_value)}")
            element_type = field_type.__args__[0]  # Get list element type (str)
            # Validate each element matches expected type
            if not all(isinstance(item, element_type) for item in field_value):
                raise ValueError(f"Invalid type in list for {field_name}")
            
        # Handle basic types (str, bool)
        else:
            # Python's type system handles basic type conversion:
            # - JSON true/false automatically becomes Python True/False
            # - strings remain strings
            # - numbers become int/float as appropriate
            if not isinstance(field_value, field_type):
                raise ValueError(
                    f"Field {field_name} expected {field_type}, got {type(field_value)}"
                )
```

The dataclasses defined in `config_setup.py` are passed to the `_create_dataclass_instance()` helper function as an argument (initially passed to `get_config()`).  

### Type Validation
The ChecksConfig and SpexConfig dataclasses define the data types for specific metadata fields. For example:

```python
@dataclass
class ChecksConfig:
    outputs: OutputsConfig
    fixity: FixityConfig
    tools: ToolsConfig
```

For each field, `_create_dataclass_instance()` looks at the type:

- For "outputs" -> creates `OutputsConfig` instance
- For "fixity" -> creates `FixityConfig` instance
- For "tools" -> creates `ToolsConfig` instance with nested tool configs

The values for the different fields is populated from the json configs. As described above, the most recent values from the last used config are deep merged when the config is first loaded. 

The `_create_dataclass_instance()` implements Type validation, ensuring inputs from the JSON match the expected type defined in `config_setup.py`.

The individual checks are:

```python
# For basic types (str, bool)
if not isinstance(field_value, field_type):
    raise ValueError(f"Field {field_name} expected {field_type}, got {type(field_value)}")

# For lists
if str(field_type).startswith('typing.List'):
    if not isinstance(field_value, list):
        raise ValueError(f"Expected list for {field_name}")

# For nested dataclasses
if hasattr(field_type, '__dataclass_fields__'):
    if not isinstance(field_value, dict):
        raise ValueError(
            f"Expected dict for nested dataclass {field_name}"
        )
    # Recursively validate nested structure
    processed_data[field_name] = self._create_dataclass_instance(
        field_type, field_value
    )

# For nested dataclasses
if hasattr(field_type, '__dataclass_fields__'):
    if not isinstance(field_value, dict):
        raise ValueError(
            f"Expected dict for nested dataclass {field_name}"
        )
    # Recursively validate nested structure
    processed_data[field_name] = self._create_dataclass_instance(
        field_type, field_value
    )
```

Here is an example from the Checks config JSON, which controls the options selected for qct-parse:

```json
"qct_parse": {
    "run_tool": "yes",        // string
    "barsDetection": true,    // boolean
    "evaluateBars": true,     // boolean
    "contentFilter": [],      // List[str]
    "profile": [],           // List[str]
    "tagname": null,         // Optional[str]
    "thumbExport": true      // boolean
}
```

Validation process:

```python
# JSON input
data = {
    "run_tool": "yes",        # Stays string
    "barsDetection": true,    # Becomes Python True
    "contentFilter": [],      # Validated as empty List[str]
    "tagname": null,         # Becomes Python None
}

# Validation checks:
1. Check all required fields exist
   - Missing 'evaluateBars' would raise error
   
2. Check type compatibility
   - If "barsDetection": "true" (string) -> Error: expected bool
   - If "contentFilter": "[]" (string) -> Error: expected list
   
3. Check nested structures
   - Lists must contain correct type
   - Optional fields can be null
   - Nested objects must match their dataclass structure
```

### Entry Points for Configuration Creation
The first instance of the ChecksConfig and SpexConfig are loaded at different point of the process in the CLI and GUI modes.  

**GUI Mode**   
In `gui_main_window.py`, the configuration objects are first created when the main window is initialized:
```python
self.config_mgr = ConfigManager()
self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
self.spex_config = self.config_mgr.get_config('spex', SpexConfig)
```

**CLI Mode**    
In `av_spex_the_file.py`, the global config_mgr is created, but the first actual retrieval of configurations happens during command processing, in the AVSpexProcessor:   

```python
# In AVSpexProcessor.__init__
self.config_mgr = ConfigManager()
self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
self.spex_config = self.config_mgr.get_config('spex', SpexConfig)
```

## Editing Configs

The ConfigManager provides mechanisms for editing the Checks and Spex configs through the CLI or UI. These include targeted updates to specific fields, applying predefined profiles, and saving the updated configurations to persist changes between sessions.

### Updating Individual Settings

The `update_config()` method enables precise updates to configuration values while maintaining the dataclass structure:

```python
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
```

This method:
- Recursively traverses nested dataclass structures
- Updates values at any level of nesting
- Maintains type validation through the dataclass framework
- Reports errors for non-existent fields

#### GUI Integration

The GUI uses this mechanism to handle checkbox state changes:

```python
def on_checkbox_changed(self, state, path):
    """Handle changes in yes/no checkboxes"""
    new_value = 'yes' if Qt.CheckState(state) == Qt.CheckState.Checked else 'no'
    
    if path[0] == "tools" and len(path) > 2:
        tool_name = path[1]
        field = path[2]
        updates = {'tools': {tool_name: {field: new_value}}}
    else:
        section = path[0]
        field = path[1]
        updates = {section: {field: new_value}}
        
    self.config_mgr.update_config('checks', updates)
```

This allows each checkbox in the interface to directly modify its corresponding field in the configuration, with changes immediately reflected in the in-memory configuration.

### Applying Predefined Profiles

The system supports applying predefined configuration profiles that modify multiple settings at once through the `apply_profile()` function:

```python
def apply_profile(profile_dict: dict):
    """Apply a predefined profile to the checks config.
    
    Args:
        profile_dict (dict): Dictionary containing the profile settings
    """
    checks_config = config_mgr.get_config('checks', ChecksConfig)
    
    # Update tool settings recursively
    for section, section_values in profile_dict.items():
        if section == 'tools':
            for tool_name, tool_settings in section_values.items():
                # Get the current tool settings
                if hasattr(checks_config.tools, tool_name):
                    tool_obj = getattr(checks_config.tools, tool_name)
                    
                    # Apply each setting
                    for key, value in tool_settings.items():
                        if hasattr(tool_obj, key):
                            setattr(tool_obj, key, value)
                        else:
                            logger.error(f"Invalid tool setting: {tool_name}.{key}")
        elif hasattr(checks_config, section):
            section_obj = getattr(checks_config, section)
            
            # Apply each setting in the section
            for key, value in section_values.items():
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                else:
                    logger.error(f"Invalid setting: {section}.{key}")
    
    # Save the updated config
    config_mgr.set_config('checks', checks_config)
```

Predefined profiles are stored as dictionaries in `config_edit.py`:

```python
profile_step1 = {
    'tools': {
        'mediainfo': {'check_tool': 'yes', 'run_tool': 'yes'},
        'ffprobe': {'check_tool': 'yes', 'run_tool': 'yes'},
        'mediaconch': {'run_mediaconch': 'yes'},
        'qctools': {'run_tool': 'yes'},
        'qct_parse': {'run_tool': 'yes'},
        'exiftool': {'check_tool': 'yes', 'run_tool': 'yes'}
    },
    'fixity': {'check_fixity': 'yes'}
}
```

This approach allows for quick application of common configuration groups, such as turning on a set of tools for common workflow steps.

### Specialized Configuration Updates

For domain-specific configuration areas like signal flow profiles, specialized update functions are provided:

```python
def apply_signalflow_profile(selected_profile: dict):
    """Apply signalflow profile changes to spex_config.
    
    Args:
        selected_profile (dict): The signalflow profile to apply (encoder settings)
    """
    spex_config = config_mgr.get_config('spex', SpexConfig)
    
    # Validate input
    if not isinstance(selected_profile, dict):
        logger.critical(f"Invalid signalflow settings: {selected_profile}")
        return
    
    # Update mediatrace_values.ENCODER_SETTINGS
    for key, value in selected_profile.items():
        if hasattr(spex_config.mediatrace_values.ENCODER_SETTINGS, key):
            setattr(spex_config.mediatrace_values.ENCODER_SETTINGS, key, value)
    
    # Now update ffmpeg_values.format.tags.ENCODER_SETTINGS if it exists
    if (hasattr(spex_config, 'ffmpeg_values') and 
        'format' in spex_config.ffmpeg_values and 
        'tags' in spex_config.ffmpeg_values['format']):
        
        # Initialize ENCODER_SETTINGS as a dict if needed
        if 'ENCODER_SETTINGS' not in spex_config.ffmpeg_values['format']['tags'] or \
           spex_config.ffmpeg_values['format']['tags']['ENCODER_SETTINGS'] is None:
            spex_config.ffmpeg_values['format']['tags']['ENCODER_SETTINGS'] = {}
            
        # Update the settings
        for key, value in selected_profile.items():
            spex_config.ffmpeg_values['format']['tags']['ENCODER_SETTINGS'][key] = value
    
    # Save the updated config
    config_mgr.set_config('spex', spex_config)
    
    # Save the last used config
    config_mgr.save_last_used_config('spex')
```

This function handles the specific complexities of updating the signal flow configuration, ensuring that settings are applied correctly to all relevant parts of the nested structure.

### CLI Configuration Management

The command-line interface provides options for targeted configuration changes through the `--on` and `--off` flags, which are processed by the `toggle_on()` and `toggle_off()` functions:

```python
def update_tool_setting(tool_names: List[str], value: str):
    """
    Update specific tool settings using config_mgr.update_config
    Args:
        tool_names: List of strings in format 'tool.field'
        value: 'yes' or 'no' (or True/False for qct_parse)
    """
    updates = {'tools': {}}
    
    for tool_spec in tool_names:
        try:
            tool_name, field = tool_spec.split('.')
            
            # Special handling for different tools
            if tool_name == 'qct_parse':
                bool_value = True if value.lower() == 'yes' else False
                updates['tools'][tool_name] = {field: bool_value}
                
            elif tool_name == 'mediaconch':
                updates['tools'][tool_name] = {field: value}

            elif tool_name == 'fixity':
                updates['fixity'] = {}
                updates['fixity'][field] = value
                
            # Standard tools with check_tool/run_tool fields
            else:
                updates['tools'][tool_name] = {field: value}
                
        except ValueError:
            logger.warning(f"Invalid format '{tool_spec}'. Expected format: tool.field")
    
    if updates:  # Only update if we have changes
        config_mgr.update_config('checks', updates)

def toggle_on(tool_names: List[str]):
    update_tool_setting(tool_names, 'yes')

def toggle_off(tool_names: List[str]):
    update_tool_setting(tool_names, 'no')
```

This implementation allows for precise control through the command line:

```bash
# Turn on mediainfo tool
python av_spex_the_file.py --on mediainfo.run_tool

# Turn off exiftool and fixed
python av_spex_the_file.py --off exiftool.run_tool --off fixity.check_fixity
```

### Replacing Entire Configurations with `set_config()`

While `update_config()` is designed for modifying specific fields within a configuration, the `set_config()` method provides a mechanism to replace an entire configuration object:

```python
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
```

Key differences between `set_config()` and `update_config()`:

1. **Complete Replacement vs. Partial Update**:
   - `set_config()` replaces the entire configuration object in the cache
   - `update_config()` modifies specific fields while preserving the rest

2. **Input Handling**:
   - `set_config()` accepts either a complete dataclass instance or a dictionary
   - `update_config()` requires a dictionary specifying just the fields to update

3. **Type Conversion**:
   - `set_config()` handles conversion of dictionaries to dataclass instances
   - `update_config()` works with the existing dataclass structure

4. **Auto-Saving**:
   - `set_config()` automatically calls `save_last_used_config()` to persist changes
   - `update_config()` only modifies the in-memory representation

This method is typically used in specialized update functions like `apply_signalflow_profile()` after making significant changes to a configuration object:

```python
# Save the updated config
config_mgr.set_config('spex', spex_config)
```

### Persisting Configuration Changes

After modifying a configuration, changes can be persisted to disk using the `save_last_used_config()` method:

```python
def save_last_used_config(self, config_name: str) -> None:
    """
    Save the current state of a config to the user's last_used config file.
    """
    if config_name not in self._configs:
        logger.error(f"Cannot save {config_name} config - not in cache")
        return
        
    # Convert dataclass to dictionary for storage
    config_dict = dataclasses.asdict(self._configs[config_name])
    
    # Ensure user config directory exists
    user_config_dir = self.get_user_config_dir()
    os.makedirs(user_config_dir, exist_ok=True)
    
    # Save to last_used_{config_name}_config.json
    config_path = os.path.join(
        user_config_dir, 
        f"last_used_{config_name}_config.json"
    )
    
    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=4)
        
    logger.debug(f"Saved {config_name} config to {config_path}")
```

This method:
1. Converts the dataclass instance to a dictionary
2. Ensures the user configuration directory exists
3. Writes the configuration to a JSON file named `last_used_{config_name}_config.json`

Persisted configurations are automatically loaded and merged with default values the next time the application starts, as described in the "The Merge Process" section.