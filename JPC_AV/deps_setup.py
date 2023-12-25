import sys
import shutil

def check_py_version():
    if sys.version_info[:2] < (3, 10):
        print("This project requires Python 3.10 or higher.")
        sys.exit(1)

def check_external_dependency(command):
    return shutil.which(command) is not None

required_commands = ['ffmpeg', 'mediainfo', 'exiftool', 'mediaconch']

check_py_version()

if __name__ == "__main__":
    for command in required_commands:
        if not check_external_dependency(command):
            print(f"Error: {command} not found. Please install it.")
            sys.exit(1)

