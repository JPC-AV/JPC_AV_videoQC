# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

## Introduction:
![Alt text](https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/av_spex_the_logo.png?raw=true)
This repository stores python scripts designed to help process digital audio and video media created from analog sources. The scripts will confirm that the digital files conform to predetermined specifications. 

----

## Requirements

### Python Version
- Python 3.10 or higher is required.

### Installation
Below are the instructions for setting up a compatible Python environment using Conda, although Conda is optional - any Python 3.10+ environment should be compatible.

#### Setting Up Conda
1. **Install Conda:**
   - Via Homebrew: `brew install --cask anaconda`
   - Alternatively, follow the installation guide on [Anaconda's official website](https://conda.io/projects/conda/en/latest/user-guide/install/macos.html).

2. **Add Conda to Your Path:**
   - Installation paths may vary based on your system's architecture (x86 or ARM).
   - For Homebrew installations:
     - ARM architecture: `export PATH="/opt/homebrew/anaconda3/bin:$PATH"`
     - x86 architecture: `export PATH="/usr/local/anaconda3/bin:$PATH"`
     - If you are unsure which of these paths to use, you can check by running `brew --prefix`

3. **Initialize Conda:**
   - For Bash: `conda init`
   - For Zsh: `conda init zsh`
   - To check your shell, run: `echo $SHELL`

#### Create an Isolated Environment
- To create an environment with the required Python version:
  ```bash
  conda create -n JPC_AV python=3.10.13
  ```

### Required Command Line Tools

The following command line tools are necessary and must be installed separately:
- MediaConch
- MediaInfo
- Exiftool
- ffmpeg
- QCTools

## Installation of AV Spex Scripts

### Initial Setup

1. **Navigate to the Project Root Directory:**
   ```bash
   cd path-to/JPC_AV/JPC_AV_videoQC
   ```

2. **Install the AV Spex Scripts in Editable Mode:**
   ```bash
   python -m pip install -e .
   ```

Verify the installation by running:
```bash
av-spex --help
```

## Usage
<img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/germfree_eq.png" alt="graphic eq image" style="width:200px;"/>

Execute the scripts with:
```bash
av-spex [path/to/directory] (*optionally:) [path/to/another/directory] [path/to/another/directory]
```

The following options are available:
```bash
usage: av-spex [-h] [--version] [-dr] [--profile {step1,step2,off}]
               [-t {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}]
               [--on {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}]
               [--off {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}]
               [-sn {JPC_AV_SVHS,BVH3100}] [-fn {jpc,bowser}]
               [-sp {config,command}] [-d] [-f]
               [paths ...]

positional arguments:
  paths                 Path to the input -f: video file(s) or -d:
                        directory(ies)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -dr, --dryrun         Flag to run av-spex w/out outputs or checks. Use to
                        change config profiles w/out processing video.
  --profile {step1,step2,off}
                        Select processing profile ('step1' or 'step2'), or
                        turn all checks off with 'off'
  -t {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}, --tool {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select individual tools to enable - turns all other
                        tools off
  --on {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select specific tools to turn on
  --off {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select specific tools to turn off
  -sn {JPC_AV_SVHS,BVH3100}, --signalflow {JPC_AV_SVHS,BVH3100}
                        Select signal flow config type (JPC_AV_SVHS or
                        BVH3100)
  -fn {jpc,bowser}, --filename {jpc,bowser}
                        Select file name config type (jpc or bowser)
  -sp {config,command}, --saveprofile {config,command}
                        Flag to write current config.yaml or
                        command_config.yaml settings to new a yaml file, for
                        re-use or reference. Select config or command:
                        --saveprofile command
  -d, --directory       Flag to indicate input is a directory
  -f, --file            Flag to indicate input is a video file
  ```

Options explain in detail below.

### Logging
Each time AV Spex is run a log file is created. Everything output to the terminal is also recorded in a log file w/ timestamps located at:
```
logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log
```

### File Validation
File naming
- AV Spex checks if the video file follows the JPC_AV naming convention (e.g., `JPC_AV_00001.mkv`). The script exits if the naming convention is not met.

Multiple fixity checks are built-in to AV Spex, which can be enabled or disabled in the `config/command_config.yaml` file.
- **Fixity**:
   - Generate and write md5 checksum to [input_video_file_name]_YYY_MM_DD_fixity.txt file
   - Read md5 checksums from text files in the input directory that end with '_checksums.md5' or '_fixity.txt' and validate against calculated md5. Record result to [input_video_file_name]_YYY_MM_DD_fixity_check.txt
- **Stream fixity**:
   - Calculate video stream and audio stream md5 checksums using the ffmpeg command: `ffmpeg -loglevel error -i {input_video} -map 0 -f streamhash -hash md5 - `
   - Read existing audio and video 'streamhash' md5s found embedded in the input mkv video file with the tags `VIDEO_STREAM_HASH` or `AUDIO_STREAM_HASH` and validate against calculated md5

### Metadata Tools
- Various metadata tools are run on the input video file(s), which can be enabled or disabled in the `config/command_config.yaml` file.
- Tools include:
  - **MediaConch**: Checks compliance with specific policies (stored as XML files in /config/ directory). [MediaConch website](https://mediaarea.net/MediaConch).
  - **MediaInfo**: Provides unified display of the most relevant technical and tag data for video and audio files. [MediaInfo website](https://mediaarea.net/en/MediaInfo).
  - **Exiftool**: Command-line application for reading metadata [Exiftool website ](https://exiftool.org/)
  - **ffprobe**: Gathers information from multimedia streams and prints it in JSON format. [ffprobe website](https://www.ffmpeg.org/ffprobe.html)
  - **QCTools**: Creates audiovisual analytics reports as XML files. [QCTools website](https://bavc.org/programs/preservation/preservation-tools/)

### Configuration
The 2 yaml files in the `/config/` directory control various settings and options. Both files can be modified manually, but it is preferable to edit the file using the command line options.   
- **command_config.yaml**:
   - The command_config.yaml stores settings pertaining to which output, tools and checks will be run.
   - Outputs ('yes'/'no'):
      - access file
      - report
      - fixity
      - stream fixity
      - overwrite stream fixity (if found)
   - Tools ('yes'/'no'):        
      - exiftool
      - ffprobe
      - mediaconch
         -  mediaconch_policy: file name from any xml file in the config directory
      - mediainfo
      - mediatrace (checks custom mkv tags)
      - qctools
      - qct-parse (more on qct-parse below)
   - Each tool has a 'run' or 'check' option    
      - **'run'** outputs a sidecar file     
      - **'check'** compares the values in the sidecar file to the values stored in the config.yaml file
- **config.yaml**:
   - Expected metadata output values are stored in `config/config.yaml`
   - Values are organized by tool
   - Multiple acceptable values are written in a list:
      ```
      Format:
      - FLAC
      - PCM
      ```
- **Options**
   - Edit the config files using command line options in order to maintain consistent formatting
   - `--profile`: Selects a predefined processing profile of particular tools outputs and checks    
      - Options: `step1`, `step2`, `allOff`
   - `--tool/-t`: Enables only the specified tool(s) and disables all others. 
      - List multiple tools in this format: `-t exiftool -t mediainfo -t ffprobe`
   - `--on`: Enables the specified tool without affecting others.
   - `--off`: Disables the specified tool without affecting others.
   - `--signalflow/-sn`: Changes the expected values in the config.yaml file for the mkv tag `ENCODER_SETTINGS` according to NMAAHC custom metadata convention   
      - Options: `JPC_AV_SVHS`, `BVH3100`
   - `--filename/-fn`: Changes the expected values in the config.yaml for the input file naming convention
      - Options: `jpc`, `bowser`
   - To edit either fo the configs without running AV Spex on an input file use the `--dryrun/-dr` option

### qct-parse
   To check the QCTools report, AV Spex incorporates code from the open source tool [qct-parse](https://github.com/amiaopensource/qct-parse). qct-parse can be used to check for individual tags, profiles, or specific content.   
#### qct-parse Options**
   - **Bars detection**: Find color bars, if present, and output start and end timestamp
   - **Evaluate bars**: Identify maximum and minimum values for Y, Cb, Cr and Saturation in color bars. Using these maximums and minimums as thresholds, evaluate the rest of the video for values outside these values.
   - **Content filter**: Identify specific content types by their QCTools report values. For example, segments fo all black. 
   - **Profile**: Evaluate QCTools report values against a set of thresholds (called a 'profile'). Returns the percentage of frames outside of those thresholds per tag.
   - **Tag name**: Set ad hoc thresholds per tag, using the following format: ` - [YMIN, lt, 100] `
   - **Thumb export**: Export thumbnail png image files for frames outside of set thresholds, limit is currently set as 1 thumbnail maximum for every 5 minutes of input video duration 

### Output
- Outputs are saved in a subdirectory within the input directory named: [input_directory_name]_qc_metadata and [input_directory_name]_report_csvs
   - **qc_metadata**:  Metadata outputs for: fixity check, exiftool, ffprobe, mediaconch, mediainfo, mediatrace, and qctools
   - **report_csvs**: CSV files used to populate the HTML report summarizing the outputs
- An HTML file is output which collects the various outputs of AV Spex and presents them as a report named: [input_directory_name]_avspex_report.html
- Any existing vrecord metadata is moved to a subdirectory named: [input_directory_name]_vrecord_metadata 

<img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/germfree_eq.png" alt="graphic eq image" style="width:200px;"/>
---

## Contributing
Contributions that enhance script functionality are welcome. Please ensure compatibility with Python 3.10 or higher.

## Acknowledgements 
AV Spex makes use of code from several open source projects. Attribution and copyright notices are included as comments inline where open source code is used.    
The copyright notices are reproduced here:

[loglog](https://github.com/amiaopensource/loglog)
```
Copyright (C) 2021  Eddy Colloton and Morgan Morel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 3 as published by
    the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

[qct-parse](https://github.com/amiaopensource/qct-parse)
```
Copyright (C) 2016 Brendan Coates and Morgan Morel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 3 as published by
    the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

[IFIscripts](https://github.com/kieranjol/IFIscripts)
```
MIT License

    Copyright (c) 2015-2018 Kieran O'Leary for the Irish Film Institute.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
```

