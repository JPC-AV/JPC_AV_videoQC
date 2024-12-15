# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

## Introduction:
![Alt text](https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/logo_image_files/av_spex_the_logo.png?raw=true)
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
   pip install -e .
   ```

Verify the installation by running:
```bash
av-spex --help
```

There is a unresolved bug in the installation process. After installing, if you are getting a PyQt6 error message, reactivate your virtual environment.
For conda this would be:
```bash
conda activate JPC_AV
```
This should resolve the PyQt6 error message until I find a better solution. 

## GUI Usage
<img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/logo_image_files/germfree_eq.png" alt="graphic eq image" style="width:200px;"/>

Open the AV Spex gui with the command:
```bash
av-spex-gui
```

<div style="display: flex; justify-content: space-between;">
  <img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/avspex_gui_screenshot_01.png" alt="AV Spex GUI Screenshot 1" width="400"/>
  <img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/avspex_gui_screenshot_02.png" alt="AV Spex GUI Screenshot 2" width="400"/>
</div>

The GUI is divided into 2 tabs  - "Checks" and "Spex".   

### Checks
The "Checks" window displays the tools and commands that will be run on the imported directories.

- <b>Import Directories...</b>    
To import directories simply click the "Import Directory..." button in the GUI window or choose it from the "File" menu.    
- <b>Command Profiles</b>    
Apply a pre-determined "profile" that applies a set of command options via this dropdown menu.    
- <b>Command Options</b>    
Edit the tool selections directly using the check boxes in the *command options* window.    
- <b>Check Spex button</b>    
If you are ready to run the checks, click the "Check Spex!" button and follow the progress int he terminal window you initially launched the app from.    

### Spex
The "Spex" section displays the expected values that AV Spex will be checking imported directories against. 

- <b>Expected Values Sections</b>    
Th expected values from are drawn popular metadata tools like exiftool, MeidaInfo, and FFprobe, as well as NMAAHC specific needs like file naming profiles and embedded signal flow documentation.      
- <b>Open Section</b>     
To view any of these specifications, click the "Open Section" button.       
The expected specifications cannot be edited from the "Open Section" text box window, those are for review only.     
- <b>Spex Dropdown Menus</b>
To change the expected values of the file naming convention or the embedded signal flow documentation (checked by the MediaTrace tool), use the provided dropdown menus.

Once you have completed your Spex selections, navigate back to the Checks window to run the app using the "Check Spex!" button.


## CLI Usage
<img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main//logo_image_files/germfree_eq.png" alt="graphic eq image" style="width:200px;"/>

Execute the scripts with:
```bash
av-spex [path/to/directory]
```

### av-spex --help
```bash
    // | |       ||   / /       //   ) )                              
   //__| |       ||  / /       ((            ___        ___           
  / ___  | ____  || / /          \\        //   ) )   //___) ) \\ / / 
 //    | |       ||/ /             ) )    //___/ /   //         \/ /  
//     | |       |  /       ((___ / /    //         ((____      / /\  

usage: av-spex [-h] [--version] [-dr] [--profile {step1,step2,off}]
               [-t {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}]
               [--on {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}]
               [--off {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}] [-sn {JPC_AV_SVHS,BVH3100}]
               [-fn {jpc,bowser}] [-sp {config,command}] [-pp] [-d] [-f] [--gui]
               [paths ...]

av-spex 0.5.0.1

AV Spex is a python application designed to help process digital audio and video media created from analog sources.
The scripts will confirm that the digital files conform to predetermined specifications.

positional arguments:
  paths                 Path to the input -f: video file(s) or -d: directory(ies)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -dr, --dryrun         Flag to run av-spex w/out outputs or checks. Use to change config profiles w/out
                        processing video.
  --profile {step1,step2,off}
                        Select processing profile or turn checks off
  -t {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}, --tool {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select individual tools to enable
  --on {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select specific tools to turn on
  --off {exiftool,ffprobe,mediaconch,mediainfo,mediatrace,qctools}
                        Select specific tools to turn off
  -sn {JPC_AV_SVHS,BVH3100}, --signalflow {JPC_AV_SVHS,BVH3100}
                        Select signal flow config type (JPC_AV_SVHS or BVH3100
  -fn {jpc,bowser}, --filename {jpc,bowser}
                        Select file name config type (jpc or bowser)
  -sp {config,command}, --saveprofile {config,command}
                        Flag to write current config.yaml or command_config.yaml settings to new a yaml file,
                        for re-use or reference.
  -pp, --printprofile   Show current config profile.
  -d, --directory       Flag to indicate input is a directory
  -f, --file            Flag to indicate input is a video file
  --gui                 Force launch in GUI mode
  ```

<a name="options"></a> Options explained in detail [below](#options). 

### Logging
Each time AV Spex is run a log file is created. Everything output to the terminal is also recorded in a log file w/ timestamps located at:
```
logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log
```

### File Validation
#### File naming
- AV Spex checks if the video file follows the JPC_AV naming convention (e.g., `JPC_AV_00001.mkv`). The script exits if the naming convention is not met.

#### File Fixity:
   - Generate and write md5 checksum to [input_video_file_name]_YYY_MM_DD_fixity.txt file
   - Read md5 checksums from text files in the input directory that end with '_checksums.md5' or '_fixity.txt' and validate against calculated md5. Record result to [input_video_file_name]_YYY_MM_DD_fixity_check.txt
#### Stream fixity:
   - Calculate video stream and audio stream md5 checksums using the ffmpeg command: `ffmpeg -loglevel error -i {input_video} -map 0 -f streamhash -hash md5 - `
   - Read existing audio and video 'streamhash' md5s found embedded in the input mkv video file with the tags `VIDEO_STREAM_HASH` or `AUDIO_STREAM_HASH` and validate against calculated md5

### Metadata Tools
Various metadata tools are run on the input video file(s), which can be enabled or disabled in the `config/command_config.yaml` file.
- Tools include:
  - **[MediaConch](https://mediaarea.net/MediaConch)**: Checks compliance with specific policies (stored as XML files in /config/ directory).
  - **[MediaInfo](https://mediaarea.net/en/MediaInfo)**: Provides unified display of the most relevant technical and tag data for video and audio files.
  - **[Exiftool](https://exiftool.org/)**: Command-line application for reading metadata 
  - **[ffprobe](https://www.ffmpeg.org/ffprobe.html)**: Gathers information from multimedia streams and prints it in JSON format.
  - **[QCTools](https://bavc.org/programs/preservation/preservation-tools/)**: Creates audiovisual analytics reports as XML files.

### Configuration
The 2 yaml files in the `/config/` directory control various settings and options. Both files can be modified manually, but it is preferable to edit the file using the command line [options](#options).   

#### command_config.yaml:
The command_config.yaml stores settings pertaining to which output, tools and checks will be run.   
Each tool has a 'run' or 'check' option. **'run'** outputs a sidecar file. **'check'** compares the values in the sidecar file to the values stored in the config.yaml file

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
   - qct-parse (more on [qct-parse](#qct-parse) below)
           
#### config.yaml:
Expected metadata output values are stored in `config/config.yaml`    
- Values are organized by tool
- Multiple acceptable values are written in a list:
      
      Format:
         - FLAC
         - PCM

#### Options    
Edit the config files using command line options in order to maintain consistent formatting
- `--profile`: Selects a predefined processing profile of particular tools outputs and checks    
   - Options: `step1`, `step2`, `off`
- `--tool/-t`: Enables only the specified tool(s) and disables all others. 
   - List multiple tools in this format: `-t exiftool -t mediainfo -t ffprobe`
- `--on`: Enables the specified tool without affecting others.
- `--off`: Disables the specified tool without affecting others.
- `--signalflow/-sn`: Changes the expected values in the config.yaml file for the mkv tag `ENCODER_SETTINGS` according to NMAAHC custom metadata convention   
   - Options: `JPC_AV_SVHS`, `BVH3100`
- `--filename/-fn`: Changes the expected values in the config.yaml for the input file naming convention
   - Options: `jpc`, `bowser`
- To edit either fo the configs without running AV Spex on an input file use the `--dryrun/-dr` option

### <a name="qct-parse"></a>qct-parse 
   To check the QCTools report, AV Spex incorporates code from the open source tool [qct-parse](https://github.com/amiaopensource/qct-parse). qct-parse can be used to check for individual tags, profiles, or specific content.   
#### qct-parse Options
   - **Bars detection**: Find color bars, if present, and output start and end timestamp
   - **Evaluate bars**: Identify maximum and minimum values for Y, Cb, Cr and Saturation in color bars. Using these maximums and minimums as thresholds, evaluate the rest of the video for values outside these values.
   - **Content filter**: Identify specific content types by their QCTools report values. For example, segments fo all black. 
   - **Profile**: Evaluate QCTools report values against a set of thresholds (called a 'profile'). Returns the percentage of frames outside of those thresholds per tag.
   - **Tag name**: Set ad hoc thresholds per tag, using the following format: ` - [YMIN, lt, 100] `
   - **Thumb export**: Export thumbnail png image files for frames outside of set thresholds, limit is currently set as 1 thumbnail maximum for every 5 minutes of input video duration 

### Output
- Outputs are saved in a subdirectory within the input directory named: 
   - **[input_directory_name]_qc_metadata**:  Metadata outputs for: fixity check, exiftool, ffprobe, mediaconch, mediainfo, mediatrace, and qctools
   - **[input_directory_name]_report_csvs**: CSV files used to populate the HTML report summarizing the outputs
- An HTML file is output which collects the various outputs of AV Spex and presents them as a report named: [input_directory_name]_avspex_report.html
- Any existing vrecord metadata is moved to a subdirectory named: [input_directory_name]_vrecord_metadata    

<br/><br/>

<img src="https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/logo_image_files/germfree_eq.png" alt="graphic eq image" style="width:200px;"/>
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

