import os
import sys
import hashlib
import logging
from log_setup import logger

def check_fixity(directory, fixity_result_file):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_checksums.md5'):
                checksum_file_path = os.path.join(root, file)
                video_file_path = os.path.join(root, file.replace('_checksums.md5', '.mkv'))

                if os.path.exists(video_file_path):
                    # Read the MD5 checksum from the _checksums.md5 file
                    expected_checksum = read_checksum_from_file(checksum_file_path)

                    # Calculate the MD5 checksum of the video file
                    actual_checksum = hashlib_md5(video_file_path)

                    # Compare the calculated checksum with the one from the file
                    if actual_checksum == expected_checksum:
                        logger.info(f'Fixity check passed for {video_file_path}')
                        result_file = open(fixity_result_file, 'w')
                        print(f'Fixity check passed for {video_file_path}', file = result_file)
                        result_file.close()
                    else:
                        logger.critical(f'Fixity check failed for {video_file_path}')
                        result_file = open(fixity_result_file, 'w')
                        print(f'Fixity check failed for {os.path.basename(video_file_path)}\n checksum read from .md5 file = {expected_checksum}\n checksum created from MKV file = {actual_checksum}', file = result_file)
                        result_file.close()
                else:
                    logger.critical(f'Video file not found: {video_file_path}')

def read_checksum_from_file(file_path):
    with open(file_path, 'r') as checksum_file:
        content = checksum_file.read()

    # Try to find the MD5 checksum in the content
    checksum_parts = content.split()
    for part in checksum_parts:
        if len(part) == 32 and all(c in '0123456789abcdefABCDEF' for c in part):
            logger.info(f'md5 checksum from {os.path.basename(file_path)} found: {part}')
            return part

    logger.critical(f'md5 checksum not found in {file_path}')
    return None

## The function below, hashlib_md5 is a slightly modified version of the function from the open-source project IFIscripts
## More here: https://github.com/Irish-Film-Institute/IFIscripts/blob/master/scripts/copyit.py
## IFIscripts license information below:
# The MIT License (MIT)
# Copyright (c) 2015-2018 Kieran O'Leary for the Irish Film Institute.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

def hashlib_md5(filename):
    '''
    Create an md5 checksum.
    '''
    read_size = 0
    last_percent_done = 0
    md5_object = hashlib.md5()
    total_size = os.path.getsize(filename)
    logger.debug(f'Generating md5 checksum for {os.path.basename(filename)}:')
    with open(str(filename), 'rb') as file_object:
        while True:
            buf = file_object.read(2**20)
            if not buf:
                break
            read_size += len(buf)
            md5_object.update(buf)
            percent_done = 100 * read_size / total_size
            if percent_done > last_percent_done:
                sys.stdout.write('[%d%%]\r' % percent_done)
                sys.stdout.flush()
                last_percent_done = percent_done
    md5_output = md5_object.hexdigest()
    logger.debug(f'calculated md5 checksum is {md5_output}')
    return md5_output

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isdir(file_path):
        print(f"Error: {file_path} is not a directory.")
        sys.exit(1)
    check_fixity(file_path)