import os
import re
import sys

# Approved values
approved_values = {
    "Collection": "JPC",
    "MediaType": "AV",
    "FileExtension": "mkv"
}

def is_valid_filename(filename):
    # Define the regular expression pattern
    pattern = r'^{Collection}_{MediaType}_\d{{5}}\.{FileExtension}$'.format(**approved_values)
    
    # Check if the filename matches the pattern
    if re.match(pattern, filename, re.IGNORECASE):
        print(f"The file name '{filename}' is valid.")
    else:
        print(f"The file name '{filename}' does not match the naming convention.")

def validate_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        if is_valid_filename(filename):
            print(f"The file name '{filename}' is valid.")
        else:
            print(f"The file name '{filename}' does not match the naming convention.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script-name.py /path/to/your/directory")
    else:
        directory_path = sys.argv[1]
        validate_files_in_directory(directory_path)
