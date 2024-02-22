import subprocess
import os
import sys
from datetime import datetime
import logging
from log_setup import logger

def get_duration(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration', '-sexagesimal',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    duration = result.stdout.decode().strip()
    return duration

def make_access_file(video_path, output_path):
    """Create access file using ffmpeg."""
    
    logger.debug(f'Running ffmpeg on {video_path} to create access copy {output_path}')

    duration_str = get_duration(video_path)
    
    ffmpeg_command = [
        'ffmpeg',
        '-n', '-vsync', '0',
        '-hide_banner', '-progress', 'pipe:1', '-nostats', '-loglevel', 'error',
        '-i', video_path,
        '-movflags', 'faststart', '-map', '0:v', '-map', '0:a?', '-c:v', 'libx264', 
        '-vf', 'yadif=1,format=yuv420p', '-crf', '18', '-preset', 'fast', '-maxrate', '1000k', '-bufsize', '1835k', 
        '-c:a', 'aac', '-strict', '-2', '-b:a', '192k', '-f', 'mp4', output_path
    ]
    
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        ff_output = ffmpeg_process.stdout.readline()
        if not ff_output:
            break
        duration_prefix = 'out_time='
        # Convert strings to datetime objects
        duration = datetime.strptime(duration_str, '%H:%M:%S.%f')
        # Calculate the total duration in seconds
        total_duration_seconds = duration.hour * 3600 + duration.minute * 60 + duration.second + duration.microsecond / 1e6
        for line in ff_output.split('\n'):
            if line.startswith(duration_prefix):
                current_frame_str = line.split(duration_prefix)[1]
                current_frame = datetime.strptime(current_frame_str, '%H:%M:%S.%f')
                # Calculate the time difference between duration and current_frame
                time_difference = current_frame - datetime.strptime('00:00:00.000000', '%H:%M:%S.%f')
                time_difference_seconds = time_difference.total_seconds()
                percent_complete = (time_difference_seconds / total_duration_seconds) * 100
                print(f"\rFFmpeg Access Copy Progress: {percent_complete:.2f}%", end='', flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
            print("Usage: python make_access.py <mkv_file>")
            sys.exit(1)
    file_path = sys.argv[1]
    output_file = file_path.replace(".mkv", "_access.mp4")
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    make_access_file(file_path, output_file)