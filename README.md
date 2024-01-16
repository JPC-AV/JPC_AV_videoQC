# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

## Introduction:
This repository stores python scripts designed to help process digital audio and video media created from analog sources. The scripts will confirm that the digital fiels conform to predetermined specifications. 

## Requirements:
An installation script is on our Roadmap and will be implemented in the future. In the meantime please find dependencies below:

The scripts are written and tested in the follow environemnt:
`conda create -n JPC_AV python=3.10.13`

if no conda - `brew install --cask anaconda` && `export PATH="/usr/local/anaconda3/bin:$PATH"`

or

https://conda.io/projects/conda/en/latest/user-guide/install/macos.html

They make use of the following python modules which are not built-in:
`pip install -r requirements.txt`

Command line tools:
- MediaConch
- MediaInfo
- Exiftool
- ffmpeg

## Running the scripts:

Usage:
`python JPC_AV/process_file.py [path/to/video_file.mkv]`

All actions performed by process_file.py are recorded in a log file located here:`logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log`

The process_file.py will first check to ensure that the video file matches the JPC_AV file naming convention, such as `JPC_AV_00001.mkv`
If the file does not match the file naming convention, the script will exit. 

Next the script will create a directory named after the video file. The destination of the new directory is dictated by `config/config.yaml`
To change the output destination change line 2 of `config.yaml`: 
`output_path: '/Users/eddy/git_dir/JPC_AV/output'`
Please ensure the path is enclosed in single quotation marks

Once the destination directory has been created, outputs are written to the destination directory using the following metadata tools:
- MediaConch (checks files against the MediaConch poilcy in the `config/` directory)
- MediaInfo ("full" or `-f` output)
- Exiftool
- ffprobe (output in JSON format)

After the outputs are created the original video file is moved to the destination directory as well. 

The outputs of these metadata tools are then checked against expected values.
Successful checks are recorded to the log file, unsuccessful checks are recorded to the log and printed to the terminal (STOUT)
