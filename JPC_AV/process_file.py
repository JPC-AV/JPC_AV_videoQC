import os
import subprocess
import sys
import logging
import fnmatch
from log_config import setup_logger
from filename_check import approved_values, is_valid_filename

logger = setup_logger(__file__)

def create_directory(video_path):
    directory_name = os.path.splitext(os.path.basename(video_path))[0]
    directory_path = os.path.join(os.getcwd(), directory_name)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    logger.debug(f'Video file will be moved to {directory_path}')

    return directory_path

def move_video_file(video_path, destination_directory):
    video_name = os.path.basename(video_path)
    destination_path = os.path.join(destination_directory, video_name)
    logger.debug(f'{video_name} moved to {destination_directory}')
    os.rename(video_path, destination_path)

def run_command(command, input_path, output_path):
    full_command = f"{command} {input_path} > {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'{full_command}')

def run_mediaconch_command(command, input_path, output_type, output_path):
    root_dir = os.path.join(os.path.abspath(os.path.dirname(os.getcwd())))
    # logger.debug(f'{root_dir} is root_dir')
    config_dir = os.path.join(root_dir, 'config')
    for file in os.listdir(config_dir):
       if fnmatch.fnmatch(file, '*.xml'):
              policy_file = file
    policy_path = os.path.join(config_dir, policy_file)
    
    if not os.path.exists(policy_path):
        logger.critical(f'Policy file not found: {policy_file}')
    else:
        logger.debug(f'Using MediaConch policy {policy_file}')
    
    full_command = f"{command} {policy_path} {input_path} {output_type} {output_path}"

    subprocess.run(full_command, shell=True)
    logger.debug(f'{full_command}')

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: {video_path} is not a valid file.")
        sys.exit(1)

    video_name = os.path.basename(video_path)
    
    is_valid_filename(video_name)

    video_id = os.path.splitext(os.path.basename(video_name))[0]
    
    # Create a directory with the same name as the video file
    destination_directory = create_directory(video_path)
    
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    mediaconch_output_path = os.path.join(destination_directory, f'{video_id}_mediaconch_output.csv')
    run_mediaconch_command('mediaconch -p', video_path, '-oc', mediaconch_output_path)

    with open(mediaconch_output_path) as mc_file:
        if 'fail' in mc_file.read():
            logger.critical('MediaConch policy failed') 

    exiftool_output_path = os.path.join(destination_directory, f'{video_id}_exiftool_output.txt')
    run_command('exiftool', video_path, exiftool_output_path)

    mediainfo_output_path = os.path.join(destination_directory, f'{video_id}_mediainfo_output.txt')
    run_command('mediainfo -f', video_path, mediainfo_output_path)

    ffprobe_output_path = os.path.join(destination_directory, f'{video_id}_ffprobe_output.txt')
    run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, ffprobe_output_path)

    # Move the video file into the created directory
    move_video_file(video_path, destination_directory)

    logger.info(f'Processing complete. Output files saved in the directory:, {destination_directory}')

if __name__ == "__main__":
    main()
