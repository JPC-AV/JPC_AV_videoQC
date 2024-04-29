# JPC_AV
AV processing scripts for the Johnson Publishing Company archive

# Repository Overview
![Alt text](https://github.com/JPC-AV/JPC_AV_videoQC/blob/main/av_spex_logo.png?raw=true)
This repository stores python scripts designed to help process digital audio and video media created from analog sources. The scripts will confirm that the digital files conform to predetermined specifications. 

----

## Requirements

### Python Version
- Python 3.10 or higher is required.

### Installation
While an automated installation script is in development, users currently need to manually manage dependencies. Below are the instructions for setting up a compatible Python environment using Conda, although Conda is optional - any Python 3.10+ environment should be compatible.

#### Setting Up Conda
1. **Install Conda:**
   - Via Homebrew: `brew install --cask anaconda`
   - Alternatively, follow the installation guide on [Anaconda's official website](https://conda.io/projects/conda/en/latest/user-guide/install/macos.html).

2. **Add Conda to Your Path:**
   - Installation paths may vary based on your system's architecture (x86 or ARM).
   - For Homebrew installations:
     - ARM architecture: `export PATH="/opt/homebrew/anaconda3/bin:$PATH"`
     - x86 architecture: `export PATH="/usr/local/anaconda3/bin:$PATH"`

3. **Initialize Conda:**
   - For Bash: `conda init`
   - For Zsh: `conda init zsh`
   - To check your shell, run: `echo $SHELL`

#### Create an Isolated Environment
- To create an environment with the required Python version:
  ```bash
  conda create -n JPC_AV python=3.10.13
  ```

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

### Required Command Line Tools

The following command line tools are necessary and must be installed separately:
- MediaConch
- MediaInfo
- Exiftool
- ffmpeg
- QCTools

Verify the installation by running:
```bash
av-spex --help
```

## Usage

Execute the scripts with:
```bash
av-spex [path/to/directory]
```

### Logging
All operations are recorded in a log file located at:
```
logs/YYYY-MM-DD_HH-MM-SS_JPC_AV_log.log
```

### File Validation
- AV Spex checks if the video file follows the JPC_AV naming convention (e.g., `JPC_AV_00001.mkv`). The script exits if the naming convention is not met.

### Metadata Analysis and Configuration
- Various metadata tools are run on the video files, which can be enabled or disabled in the `config/command_config.yaml` file.
- Tools include:
  - **MediaConch**: Checks compliance with specific policies.
  - **MediaInfo**: Provides detailed file information.
  - **Exiftool**: Edits and analyzes metadata.
  - **ffprobe**: Outputs information in JSON format.
  - **QCTools**: Analyzes video quality.
- Expected output values are configured in `config/config.yaml`.

### Output and Validation
- Outputs are saved in the same directory as the input file.
- Outputs are validated against predefined expectations, with results logged and failures also printed to the terminal (STDOUT).

---

## Contributing
Contributions that enhance script functionality are welcome. Please ensure compatibility with Python 3.10 or higher.

