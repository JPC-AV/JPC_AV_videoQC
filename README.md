# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

## Introduction:
This repository stores python scripts designed to help process digital audio and video media created from analog sources. The scripts will confirm that the digital files conform to predetermined specifications. 

## Requirements:
An installation script is on our Roadmap and will be implemented in the future. In the meantime please find dependencies below:

These scripts require Python 3.10+. Any Python 3.10+ environment should be compatible, but we have included conda instructions below for those who wish to create an isolated python environment. conda is not a requirement.

The scripts are written and tested in the follow environment:
`conda create -n JPC_AV python=3.10.13`

You can install conda with homebrew: `brew install --cask anaconda` 

You need to add conda to your path. The install location for homebrew changed when Apple moved from x86 to ARM architecture. 

Confirm the location of anaconda3 after install. If you installed it with homebrew it will be here:
    `/opt/homebrew/anaconda3/`
or here:
    `/usr/local/anaconda3/`

Once you've located anaconda3, run one the corresponding command:    
    `export PATH="/opt/homebrew/anaconda3/bin:$PATH"`    
or:     
    `export PATH="/usr/local/anaconda3/bin:$PATH"`     

or install directly from anaconda's website using this guide: https://conda.io/projects/conda/en/latest/user-guide/install/macos.html

Finally, run `conda init` or `conda init zsh` depending which shell you are using. (To check which shell you are using simply run `echo $SHELL`)


Install necessary python modules which are not built-in using pip and requirements.txt:
`pip install -r requirements.txt`

Lastly, these scripts make use of the following command line tools:
- MediaConch
- MediaInfo
- Exiftool
- ffmpeg
- QCTools

## Running the scripts:

Usage:
`python JPC_AV/process_file.py [path/to/video_file.mkv]`

All actions performed by process_file.py are recorded in a log file located here:`logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log`

The process_file.py will first check to ensure that the video file matches the JPC_AV file naming convention, such as `JPC_AV_00001.mkv`
If the file does not match the file naming convention, the script will exit. 

process_file.py will run metadata tools on the input video file. The available tools are:
- MediaConch (checks files against the MediaConch poilcy listed in 'config/command_config.yaml')
- MediaInfo ("full" or `-f` output)
- Exiftool
- ffprobe (output in JSON format)
- QCTools

These tools can be toggled on/off by changing the config/command_config.yaml file. Set tools to 'yes' to run them 'no' to turn them off. 

Outputs are written to the same directory as the input file.

The outputs of these metadata tools are then checked against expected values. 

Expected values are stored in config/config.yaml. These checks can be turned on or off from config/command_config.yaml

Successful checks are recorded to the log file, unsuccessful checks are recorded to the log, saved to a CSV called {filename}_metadata_difference_YYYYMMDD_HH-MM-SS.csv, and printed to the terminal (STOUT).
