import os
import subprocess
import sys
import logging
from filename_check import approved_values, is_valid_filename

def create_directory(video_path):
    directory_name = os.path.splitext(os.path.basename(video_path))[0]
    directory_path = os.path.join(os.getcwd(), directory_name)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    return directory_path

def move_video_file(video_path, destination_directory):
    video_name = os.path.basename(video_path)
    destination_path = os.path.join(destination_directory, video_name)
    os.rename(video_path, destination_path)

def run_command(command, input_path, output_path):
    full_command = f"{command} {input_path} > {output_path}"

    subprocess.run(full_command, shell=True)

def mediaconch_command():
    policy_file = os.path.join(os.getcwd(), 'JPC_AV_NTSC_MKV.xml')
    if not os.path.exists(policy_file):
        logging.critical(f'Policy file not found: {policy_file}')
    else:
        logging.debug(f'Using MediaConch policy {policy_file}')
    
    mediaconch_output_path = os.path.join(destination_directory, f'{file_name}_mediaconch_output.csv')
    #mediaconch_command = print(f'mediaconch -p ' + policy_file)
    run_command('mediaconch', video_path, mediaconch_output_path)
    with open(mediaconch_output_path) as mc_file:
        if 'fail' in mc_file.read():
            print('MediaConch policy failed')

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: {video_path} is not a valid file.")
        sys.exit(1)

    is_valid_filename(video_path)
    
    # Create a directory with the same name as the video file
    destination_directory = create_directory(video_path)
    
    # Run exiftool, mediainfo, and ffprobe on the video file and save the output to text files
    exiftool_output_path = os.path.join(destination_directory, f'{file_name}_exiftool_output.txt')
    run_command('exiftool', video_path, exiftool_output_path)

    mediainfo_output_path = os.path.join(destination_directory, f'{file_name}_mediainfo_output.txt')
    run_command('mediainfo -f', video_path, mediainfo_output_path)

    ffprobe_output_path = os.path.join(destination_directory, f'{file_name}_ffprobe_output.txt')
    run_command('ffprobe -v error -hide_banner -show_format -show_streams -print_format json', video_path, ffprobe_output_path)

    # Move the video file into the created directory
    move_video_file(video_path, destination_directory)

    print("Processing complete. Output files saved in the directory:", destination_directory)

if __name__ == "__main__":
    main()
