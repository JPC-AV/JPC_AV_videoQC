# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

## Introduction:
![Alt text](https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/av_spex_logo.png?raw=true)
This repository stores python scripts designed to help process digital audio and video media created from analog sources. The scripts will confirm that the digital files conform to predetermined specifications. 

## Requirements:

#### Environment
These scripts require Python 3.10+. Any Python 3.10+ environment should be compatible, but we have included conda instructions below for those who wish to create an isolated python environment. conda is not a requirement.

The scripts are written and tested in the follow environment:
`conda create -n JPC_AV python=3.10.13`

You can install conda with homebrew: `brew install --cask anaconda` 

You need to add conda to your path. The install location for homebrew changed when Apple moved from x86 to ARM architecture. 

Confirm the location of anaconda3 after install. If you installed it with homebrew it will be here:
`/opt/homebrew/anaconda3/` or here: `/usr/local/anaconda3/`

Once you've located anaconda3, run one the corresponding commands:    
`export PATH="/opt/homebrew/anaconda3/bin:$PATH"`    
or:     
`export PATH="/usr/local/anaconda3/bin:$PATH"`     

As an alternative to homebrew, you can install directly from anaconda's website using this guide: https://conda.io/projects/conda/en/latest/user-guide/install/macos.html

Finally, run `conda init` (for bash) or `conda init zsh` (for zsh) depending which shell you are using. (To check which shell you are using simply run `echo $SHELL`)
* * *

#### Install
Install necessary python modules and the AV Spex scripts by navigating to the root directory of the project (the directory containing the pyproject.toml file):
`cd path-to/JPC_AV/JPC_AV_videoQC`

Install the package in editable mode using pip. Run the following command from the root directory of the project:
`python -m pip install -e .`

Lastly, these scripts make use of the following command line tools:
- MediaConch
- MediaInfo
- Exiftool
- ffmpeg
- QCTools

This will install the AV Spex scripts. To call them use the command:
`process-av`

Verify the install by running:
`process-av --help`

## Running the scripts:

Usage:
`process-av [path/to/directory]`

All actions performed by process-av are recorded in a log file located here:`logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log`

The process-av will first check to ensure that the video file matches the JPC_AV file naming convention, such as `JPC_AV_00001.mkv`
If the file does not match the file naming convention, the script will exit. 

process-av will run metadata tools on the input video file. The available tools are:
- MediaConch (checks files against the MediaConch policy listed in 'config/command_config.yaml')
- MediaInfo ("full" or `-f` output)
- Exiftool
- ffprobe (output in JSON format)
- QCTools

These tools can be toggled on/off by changing the config/command_config.yaml file. Set tools to 'yes' to run them 'no' to turn them off. 

Outputs are written to the same directory as the input file.

The outputs of these metadata tools are then checked against expected values. 

Expected values are stored in config/config.yaml. These checks can be turned on or off from config/command_config.yaml

Successful checks are recorded to the log file, unsuccessful checks are recorded to the log, and printed to the terminal (STDOUT).
