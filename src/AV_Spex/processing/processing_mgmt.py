import os

from ..processing import run_tools
from ..utils import dir_setup
from ..utils.log_setup import logger
from ..utils.find_config import ChecksConfig, SpexConfig
from ..utils.config_manager import ConfigManager
from ..utils.generate_report import generate_final_report
from ..checks.fixity_check import check_fixity, output_fixity
from ..checks.mediainfo_check import parse_mediainfo
from ..checks.mediatrace_check import parse_mediatrace, create_metadata_difference_report
from ..checks.exiftool_check import parse_exiftool
from ..checks.ffprobe_check import parse_ffprobe
from ..checks.embed_fixity import validate_embedded_md5, process_embedded_fixity
from ..checks.make_access import process_access_file
from ..checks.qct_parse import run_qctparse
from ..checks.mediaconch_check import find_mediaconch_policy, run_mediaconch_command, parse_mediaconch_output


config_mgr = ConfigManager()
checks_config = config_mgr.get_config('checks', ChecksConfig)
spex_config = config_mgr.get_config('spex', SpexConfig)


def process_fixity(source_directory, video_path, video_id):
    """
    Orchestrates the entire fixity process, including embedded and file-level operations.

    Args:
        source_directory (str): Directory containing source files
        video_path (str): Path to the video file
        video_id (str): Unique identifier for the video
    """
    # Embed stream fixity if required  
    if checks_config.fixity.embed_stream_fixity == 'yes':
        process_embedded_fixity(video_path)

    # Validate stream hashes if required
    if checks_config.fixity.validate_stream_fixity == 'yes':
        if checks_config.fixity.embed_stream_fixity == 'yes':
            logger.critical("Embed stream fixity is turned on, which overrides validate_fixity. Skipping validate_fixity.\n")
        else:
            validate_embedded_md5(video_path)

    # Initialize md5_checksum variable
    md5_checksum = None

    # Create checksum for video file and output results
    if checks_config.fixity.output_fixity == 'yes':
        md5_checksum = output_fixity(source_directory, video_path)

    # Verify stored checksum and write results  
    if checks_config.fixity.check_fixity == 'yes':
        check_fixity(source_directory, video_id, actual_checksum=md5_checksum)


def process_qctools_output(video_path, source_directory, destination_directory, video_id, report_directory=None):
    """
    Process QCTools output, including running QCTools and optional parsing.
    
    Args:
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        report_directory (str, optional): Directory to save reports
        
    Returns:
        dict: Processing results and paths
    """
    results = {
        'qctools_output_path': None,
        'qctools_check_output': None
    }

    # Check if QCTools should be run
    if checks_config.tools['qctools']['run_qctools'] != 'yes':
        return results

    # Prepare QCTools output path
    qctools_ext = checks_config.outputs['qctools_ext']
    qctools_output_path = os.path.join(destination_directory, f'{video_id}.{qctools_ext}')
    
    try:
        # Run QCTools command
        run_tools.run_command('qcli -i', video_path, '-o', qctools_output_path)
        logger.debug('')  # Add new line for cleaner terminal output
        results['qctools_output_path'] = qctools_output_path

        # Check QCTools output if configured
        if checks_config.tools['qctools']['check_qctools'] == 'yes':
            # Ensure report directory exists
            if not report_directory:
                report_directory = dir_setup.make_report_dir(source_directory, video_id)

            # Verify QCTools output file exists
            if not os.path.isfile(qctools_output_path):
                logger.critical(f"Unable to check qctools report. No file found at: {qctools_output_path}\n")
                return results

            # Run QCTools parsing
            run_qctparse(video_path, qctools_output_path, report_directory)
            # currently not using results['qctools_check_output']

    except Exception as e:
        logger.critical(f"Error processing QCTools output: {e}")

    return results


def process_video_outputs(video_path, source_directory, destination_directory, video_id, metadata_differences):
    """
    Coordinate the entire output processing workflow.
    
    Args:
        video_path (str): Path to the input video file
        source_directory (str): Source directory for the video
        destination_directory (str): Destination directory for output files
        video_id (str): Unique identifier for the video
        metadata_differences (dict): Differences found in metadata checks
        
    Returns:
        dict: Processing results and file paths
    """

    # Collect processing results
    processing_results = {
        'metadata_diff_report': None,
        'qctools_output': None,
        'access_file': None,
        'html_report': None
    }

    # Create report directory if report is enabled
    report_directory = None
    if checks_config.outputs['report'] == 'yes':
        report_directory = dir_setup.make_report_dir(source_directory, video_id)
        # Process metadata differences report
        processing_results['metadata_diff_report'] = create_metadata_difference_report(
                metadata_differences, report_directory, video_id
            )
    else:
         processing_results['metadata_diff_report'] =  None

    # Process QCTools output
    process_qctools_output(
        video_path, source_directory, destination_directory, video_id, report_directory
    )

    # Generate access file
    processing_results['access_file'] = process_access_file(
        video_path, source_directory, video_id
    )

    # Generate final HTML report
    processing_results['html_report'] = generate_final_report(
        video_id, source_directory, report_directory, destination_directory
    )

    return processing_results


def check_tool_metadata(tool_name, output_path):
    """
    Check metadata for a specific tool if configured.
    
    Args:
        tool_name (str): Name of the tool
        output_path (str): Path to the tool's output file
        
    Returns:
        dict or None: Differences found by parsing the tool's output, or None
    """
    # Mapping of tool names to their parsing functions
    parse_functions = {
        'exiftool': parse_exiftool,
        'mediainfo': parse_mediainfo,
        'mediatrace': parse_mediatrace,
        'ffprobe': parse_ffprobe
    }

    # Check if tool metadata checking is enabled
    if output_path and checks_config.tools[tool_name][f'check_{tool_name}'] == 'yes':
        parse_function = parse_functions.get(tool_name)
        if parse_function:
            return parse_function(output_path)
    
    return None


def process_video_metadata(video_path, destination_directory, video_id):
    """
    Main function to process video metadata using multiple tools.
    
    Args:
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        
    Returns:
        dict: Dictionary of metadata differences from various tools
    """
    # List of tools to process
    tools = ['exiftool', 'mediainfo', 'mediatrace', 'ffprobe']
    
    # Store differences for each tool
    metadata_differences = {}
    
    # Process each tool
    for tool in tools:
        # Run tool and get output path
        output_path = run_tools.run_tool_command(tool, video_path, destination_directory, video_id)
        
        # Check metadata and store differences
        differences = check_tool_metadata(tool, output_path)
        if differences:
            metadata_differences[tool] = differences
    
    return metadata_differences


def validate_video_with_mediaconch(video_path, destination_directory, video_id, config_path):
    """
    Coordinate the entire MediaConch validation process.
    
    Args:
        video_path (str): Path to the input video file
        destination_directory (str): Directory to store output files
        video_id (str): Unique identifier for the video
        config_path (object): Configuration path object
        
    Returns:
        dict: Validation results from MediaConch policy check
    """
    # Check if MediaConch should be run
    if checks_config.tools['mediaconch']['run_mediaconch'] != 'yes':
        logger.info("MediaConch validation skipped")
        return {}

    # Find the policy file
    policy_path = find_mediaconch_policy(config_path)
    if not policy_path:
        return {}

    # Prepare output path
    mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')

    # Run MediaConch command
    if not run_mediaconch_command(
        'mediaconch -p', 
        video_path, 
        '-oc', 
        mediaconch_output_path, 
        policy_path
    ):
        return {}

    # Parse and validate MediaConch output
    validation_results = parse_mediaconch_output(mediaconch_output_path)

    return validation_results