import os
import sys
import shutil
import re
from ..utils.log_setup import logger
from ..utils.find_config import config_path

def validate_input_paths(input_paths, is_file_mode):
    source_directories = []
    for input_path in input_paths:
        try:
            if is_file_mode and not os.path.isfile(input_path):
                raise ValueError(f"Error: {input_path} is not a valid file.")
            elif not is_file_mode and not os.path.isdir(input_path):
                raise ValueError(f"Error: {input_path} is not a valid directory.")
            
            directory = os.path.dirname(input_path) if is_file_mode else input_path
            source_directories.append(directory)
            logger.info(f'Input directory found: {directory}\n')
        except ValueError as e:
            logger.critical(str(e))
            sys.exit(1)
    return source_directories


def move_vrec_files(directory, video_id):
    vrecord_files_found = False

    # Create the target directory path
    vrecord_directory = os.path.join(directory, f'{video_id}_vrecord_metadata')

    # Check if the vrecord directory already exists and contains the expected files
    if os.path.exists(vrecord_directory):
        expected_files = [
            '_QC_output_graphs.jpeg',
            '_vrecord_input.log',
            '_capture_options.log',
            '.mkv.qctools.mkv',
            '.framemd5'
        ]

        # Check if at least one expected file is in the vrecord directory
        if any(filename.endswith(ext) for ext in expected_files for filename in os.listdir(vrecord_directory)):
            logger.debug(f"Existing vrecord files found in {os.path.basename(directory)}/{os.path.basename(vrecord_directory)}\n")
            return

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if the file matches the naming convention
        if (
            os.path.isfile(file_path)
            and filename.endswith(('_QC_output_graphs.jpeg', '_vrecord_input.log', '_capture_options.log', '.mkv.qctools.mkv', '.framemd5'))
        ):
            # Create the target directory if it doesn't exist
            vrecord_directory = os.path.join(directory, f'{video_id}_vrecord_metadata')
            os.makedirs(vrecord_directory, exist_ok=True)
            # Move the file to the target directory
            new_path = os.path.join(vrecord_directory, filename)
            shutil.move(file_path, new_path)
            # logger.debug(f'Moved vrecord file: {filename} to directory: {os.path.basename(vrecord_directory)}')
            vrecord_files_found = True

    # Check if any matching files were found to create the directory
    if vrecord_files_found:
        logger.debug(f"Files generated by vrecord found. '{video_id}_vrecord_metadata' directory created and files moved.\n")
    else:
        logger.debug("No vrecord files found.\n")


def find_mkv(source_directory):
    # Create empty list to store any found mkv files
    found_mkvs = []
    for filename in os.listdir(source_directory):
        if filename.lower().endswith('.mkv'):
            if 'qctools' not in filename.lower():
                found_mkvs.append(filename)
    # check if found_mkvs is more than one
    if found_mkvs:
        if len(found_mkvs) == 1:
            video_path = os.path.join(source_directory, found_mkvs[0])
            logger.info(f'Input video file found in {source_directory}: {video_path}\n')
        else:
            logger.critical(f'More than 1 mkv found in {source_directory}: {found_mkvs}\n')
            return None
    else:
        logger.critical(f"Error: No mkv video file found in the directory: {source_directory}\n")
        return None

    return video_path


def check_directory(source_directory, video_id):
    """
    Checks whether the base name of a directory matches the given video_id.
    
    Args:
        source_directory (str): The path to the directory.
        video_id (str): The expected video ID to match.

    Returns:
        bool: True if the directory name matches the video_id, otherwise False.
    """
    directory_name = os.path.basename(source_directory)
    if directory_name.startswith(video_id):
        logger.info(f'Directory name "{directory_name}" correctly matches video file name "{video_id}".\n')
        return True
    else:
        logger.critical(f'Directory name "{directory_name}" does not correctly match the expected "{video_id}".\n')
        return False


def make_qc_output_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    destination_directory = os.path.join(source_directory, f'{video_id}_qc_metadata')

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    logger.debug(f'Metadata files will be written to {destination_directory}\n')

    return destination_directory


def make_report_dir(source_directory, video_id):
    '''
    Creates output directory for metadata files
    '''

    report_directory = os.path.join(source_directory, f'{video_id}_report_csvs')

    if os.path.exists(report_directory):
        shutil.rmtree(report_directory)
    os.makedirs(report_directory)

    logger.debug(f'Report files will be written to {report_directory}\n')

    return report_directory


def is_valid_filename(video_filename):
    '''
    Locates approved values for the file name, stored in key:value pairs under 'filename_values' in config/config.yaml.
    The file name pattern varies and is constructed dynamically depending on the provided config.
    '''
    valid_filename = False
    
    # Reads filename_values from config.yaml into dictionary approved_values
    approved_values = config_path.config_dict['filename_values']

    # Get only the base filename (not the full path)
    base_filename = os.path.basename(video_filename)

    # Build the dynamic regex pattern based on the keys in the config
    pattern_parts = [
        re.escape(approved_values['Collection']),
        re.escape(approved_values['MediaType']),
        approved_values['ObjectID']  # ObjectID can contain a regex, so no escaping
    ]
    
    # Check if 'DigitalGeneration' is part of the convention and include it in the pattern if present
    if 'DigitalGeneration' in approved_values:
        pattern_parts.append(re.escape(approved_values['DigitalGeneration']))
    
    # Append the file extension
    file_extension = re.escape(approved_values['FileExtension'])
    
    # Construct the complete pattern, joining the parts and accounting for the file extension
    pattern = r'^{0}\.{1}$'.format('_'.join(pattern_parts), file_extension)
    
    # Check if the filename matches the pattern
    if re.match(pattern, base_filename, re.IGNORECASE):
        logger.debug(f"The file name '{base_filename}' is valid.\n")
        valid_filename = True
    else:
        logger.critical(f"The file name '{base_filename}' is not valid.\n")
        valid_filename = False

    return valid_filename


if sys.argv[0] == __file__:
    if len(sys.argv) != 2:
        print("Usage: python filename_check.py /path/to/your/directory")
    else:
        video_path = sys.argv[1]
        valid_filename = is_valid_filename(video_path)


def initialize_directory(source_directory):
    """
    Prepare the directory for processing by finding the video file 
    and validating the filename.

    Args:
        source_directory (str): Path to the source directory

    Returns:
        tuple: (video_path, video_id, destination_directory) if successful
        None if preparation fails
    """
    video_path = find_mkv(source_directory)

    if video_path is None:
        logger.warning(f"Skipping {source_directory} due to error.\n")
        return None  # Indicates preparation failed

    valid_filename = is_valid_filename(video_path)

    if valid_filename is False:
        logger.warning(f"Skipping {source_directory} due to error.\n")
        return None  # Indicates preparation failed

    logger.warning(f'Now processing {video_path}\n')

    # outputs video_id (i.e. 'JPC_AV_05000')
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    # Check to confirm directory is the same name as the video file name
    check_directory(source_directory, video_id)

    # Create 'destination directory' for qc outputs
    destination_directory = make_qc_output_dir(source_directory, video_id)

    # Moves vrecord files to subdirectory  
    move_vrec_files(source_directory, video_id)

    # Iterate through files in the directory to identify access file
    access_file_found = None
    for filename in os.listdir(source_directory):
        if filename.lower().endswith('mp4'):
            access_file_found = filename
            logger.info("Existing access file found!\n")
            break

    return video_path, video_id, destination_directory, access_file_found