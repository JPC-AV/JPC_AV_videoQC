import os
import sys
import hashlib
from datetime import datetime
import logging
from log_setup import logger

def check_fixity(directory, video_id, actual_checksum=None):
    fixity_result_file = os.path.join(directory, f'{video_id}_qc_metadata', f'{video_id}_{datetime.now().strftime("%Y_%m_%d")}_fixity_check.txt')
    # Walks files of the source directory looking for file with '_checksums.md5' suffix
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_checksums.md5') or file.endswith('_fixity.txt'):
                checksum_file_path = os.path.join(root, file)
                video_file_path = os.path.join(root, f'{video_id}.mkv')
                # If video file exists, then:
                if os.path.exists(video_file_path):
                    # Read the MD5 checksum from the _checksums.md5 file
                    expected_checksum = read_checksum_from_file(checksum_file_path)
                    # If checksum has not yet been calculated, then:
                    if actual_checksum is None:
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

def output_fixity(source_directory, video_path):
    # Parse video_id from video file path
    video_id = os.path.splitext(os.path.basename(os.path.basename(video_path)))[0]
    # Create fixity results file
    fixity_result_file = os.path.join(source_directory, f'{video_id}_{datetime.now().strftime("%Y_%m_%d")}_fixity.txt')
    # Calculate the MD5 checksum of the video file
    md5_checksum = hashlib_md5(video_path)
    # Open fixity_result_file
    result_file = open(fixity_result_file, 'w')
    # Print Md5 in 'filename[tab]Checksum' format
    print(f'{os.path.basename(video_path)}\t{md5_checksum}', file = result_file)
    # Close fixity_result_file
    result_file.close()
    logger.debug(f'\nMD5 checksum written to {fixity_result_file}')
    return md5_checksum

def read_checksum_from_file(file_path):
    with open(file_path, 'r') as checksum_file:
        content = checksum_file.read()

    # Try to find the MD5 checksum in the content
    checksum_parts = content.split()
    for part in checksum_parts:
        if len(part) == 32 and all(c in '0123456789abcdefABCDEF' for c in part):
            logger.info(f'MD5 checksum found in {os.path.basename(file_path)}: {part}')
            return part

    logger.critical(f'md5 checksum not found in {file_path}')
    return None

def hashlib_md5(filename):
    '''
    Create an md5 checksum.
    '''
    read_size = 0
    last_percent_done = 0
    md5_object = hashlib.md5()
    total_size = os.path.getsize(filename)
    logger.debug(f'Generating md5 checksum for {os.path.basename(filename)} via {os.path.basename(__file__)}:')
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
    logger.info(f'Calculated md5 checksum is {md5_output}')
    return md5_output

## The function above, hashlib_md5 is a slightly modified version of the function from the open-source project IFIscripts
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isdir(file_path):
        print(f"Error: {file_path} is not a directory.")
        sys.exit(1)
    check_fixity(file_path)