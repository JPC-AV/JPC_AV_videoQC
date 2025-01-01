import os
import csv
import subprocess
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config


def run_command(command, input_path, output_type, output_path):
    '''
    Run a shell command with 4 variables: command name, path to the input file, output type (often '>'), path to the output file
    '''

    # Get the current PATH environment variable
    env = os.environ.copy()
    env['PATH'] = '/usr/local/bin:' + env.get('PATH', '')

    full_command = f"{command} \"{input_path}\" {output_type} {output_path}"

    logger.debug(f'Running command: {full_command}\n')
    subprocess.run(full_command, shell=True, env=env)


def run_tool_command(tool_name, video_path, destination_directory, video_id, command_config):
    """
    Run a specific metadata extraction tool and generate its output file.
    
    Args:
        tool_name (str): Name of the tool to run (e.g., 'exiftool', 'mediainfo')
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        command_config (object): Configuration object with tool settings
        
    Returns:
        str or None: Path to the output file, or None if tool is not run
    """
    # Define tool-specific command configurations
    tool_commands = {
        'exiftool': {
            'command': 'exiftool',
            'config_key': 'run_exiftool'
        },
        'mediainfo': {
            'command': 'mediainfo -f',
            'config_key': 'run_mediainfo'
        },
        'mediatrace': {
            'command': 'mediainfo --Details=1 --Output=XML',
            'config_key': 'run_mediatrace'
        },
        'ffprobe': {
            'command': 'ffprobe -v error -hide_banner -show_format -show_streams -print_format json',
            'config_key': 'run_ffprobe'
        }
    }

    # Check if the tool is configured to run
    tool_config = tool_commands.get(tool_name)
    if not tool_config:
        logger.error(f"tool command is not configured correctly: {tool_name}")
        return None

    # Construct output path
    output_path = os.path.join(destination_directory, f'{video_id}_{tool_name}_output.{_get_file_extension(tool_name)}')
    
    # Check if tool should be run based on configuration
    if command_config.command_dict['tools'][tool_name][tool_config['config_key']] == 'yes':
        if tool_name == 'mediatrace':
            logger.debug(f"Creating {tool_name.capitalize()} XML file to check custom MKV Tag metadata fields:")
        
        # Run the tool command
        run_command(tool_config['command'], video_path, '>', output_path)
        
    return output_path
    

def _get_file_extension(tool_name):
    """
    Get the appropriate file extension for each tool's output.
    
    Args:
        tool_name (str): Name of the tool
        
    Returns:
        str: File extension for the tool's output
    """
    extension_map = {
        'exiftool': 'txt',
        'mediainfo': 'txt',
        'mediatrace': 'xml',
        'ffprobe': 'txt'
    }
    return extension_map.get(tool_name, 'txt')

