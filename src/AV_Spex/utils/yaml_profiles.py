import argparse
from ..utils.log_setup import logger
from ..utils.find_config import ChecksConfig, SpexConfig
from ..utils.config_manager import ConfigManager

config_mgr = ConfigManager()

def apply_profile(selected_profile):
    """Apply profile changes to checks_config."""
    checks_config = config_mgr.get_config('checks', ChecksConfig)
    
    if 'outputs' in selected_profile:
        checks_config.outputs.update(selected_profile["outputs"])

    if 'tools' in selected_profile:
        for tool, updates in selected_profile["tools"].items():
            if tool in checks_config.tools:
                tool_config = checks_config.tools[tool]
                if isinstance(tool_config, dict):
                    tool_config.update(updates)
                elif hasattr(tool_config, "__dict__"):
                    for key, value in updates.items():
                        if hasattr(tool_config, key):
                            setattr(tool_config, key, value)

    if 'fixity' in selected_profile:
        for key, value in selected_profile["fixity"].items():
            if hasattr(checks_config.fixity, key):
                setattr(checks_config.fixity, key, value)
    
    config_mgr.set_config('checks', checks_config)


def apply_by_name(tool_names):
    # Get config instance
    checks_config = config_mgr.get_config('checks', ChecksConfig)
    
    # Turn all tools off first
    for tool in checks_config.tools:
        if hasattr(checks_config.tools[tool], 'run_tool'):
            checks_config.tools[tool].run_tool = 'no'
            checks_config.tools[tool].check_tool = 'no'

    # Enable specified tools
    for tool in tool_names:
        if tool in checks_config.tools:
            if hasattr(checks_config.tools[tool], 'run_tool'):
                checks_config.tools[tool].run_tool = 'yes'
                checks_config.tools[tool].check_tool = 'yes'
            logger.debug(f"{tool} set to 'on'")

    config_mgr.set_config('checks', checks_config)


def toggle_on(tool_names):
    checks_config = config_mgr.get_config('checks', ChecksConfig)
    
    for tool in tool_names:
        if tool in checks_config.tools:
            tool_config = checks_config.tools[tool]
            for field in vars(tool_config):
                setattr(tool_config, field, 'yes')
            logger.debug(f"{tool} set to 'on'")

    config_mgr.set_config('checks', checks_config)


def toggle_off(tool_names):
    checks_config = config_mgr.get_config('checks', ChecksConfig)
    
    for tool in tool_names:
        if tool in checks_config.tools:
            tool_config = checks_config.tools[tool]
            for field in vars(tool_config):
                setattr(tool_config, field, 'no')
            logger.debug(f"{tool} set to 'off'")

    config_mgr.set_config('checks', checks_config)


profile_step1 = {
    "tools": {
        "qctools": {
            "check_tool": "no",
            "run_tool": "no"   
        },
        "exiftool": {
            "check_tool": "yes",
            "run_tool": "yes"
        },
        "ffprobe": {
            "check_tool": "no",
            "run_tool": "yes"
        },
        "mediaconch": {
            "mediaconch_policy": "JPC_AV_NTSC_MKV_2024-09-20.xml",
            "run_mediaconch": "yes"
        },
        "mediainfo": {
            "check_tool": "yes",
            "run_tool": "yes"
        },
        "mediatrace": {
            "check_tool": "yes",
            "run_tool": "yes"
        }
    },
    "outputs": {
        "access_file": "no",
        "report": "no",
        "qctools_ext": "qctools.xml.gz"
    },
    "fixity": {
        "check_fixity": "no",
        "validate_stream_fixity": "no",
        "embed_stream_fixity": "yes",
        "output_fixity": "yes",
        "overwrite_stream_fixity": "no"
    }
}

profile_step2 = {
    "tools": {
        "exiftool": {
            "check_tool": "yes",
            "run_tool": "no"
        },
        "ffprobe": {
            "check_tool": "yes",
            "run_tool": "no"
        },
        "mediaconch": {
            "mediaconch_policy": "JPC_AV_NTSC_MKV_2024-09-20.xml",
            "run_mediaconch": "yes"
        },
        "mediainfo": {
            "check_tool": "yes",
            "run_tool": "no"
        },
        "mediatrace": {
            "check_tool": "yes",
            "run_tool": "no"
        },
        "qctools": {
            "check_tool": "yes",
            "run_tool": "yes"
        },
        "qct-parse": {
            "barsDetection": True,
            "evaluateBars": True,
            "contentFilter": {"profile": ""},
            "tagname": None,
            "thumbExport": True
        }
    },
    "outputs": {
        "access_file": "no",
        "report": "yes",
        "qctools_ext": "qctools.xml.gz"
    },
    "fixity": {
        "check_fixity": "yes",
        "validate_stream_fixity": "yes",
        "embed_stream_fixity": "no",
        "output_fixity": "no",
        "overwrite_stream_fixity": "no"
    }
}

profile_allOff = {
    "tools": {
        "exiftool": {
            "check_tool": "no",
            "run_tool": "no"
        },
        "ffprobe": {
            "check_tool": "no",
            "run_tool": "no"
        },
        "mediaconch": {
            "mediaconch_policy": "JPC_AV_NTSC_MKV_2024-09-20.xml",
            "run_mediaconch": "no"
        },
        "mediainfo": {
            "check_tool": "no",
            "run_tool": "no"
        },
        "mediatrace": {
            "check_tool": "no",
            "run_tool": "no"
        },
        "qctools": {
            "check_tool": "no",
            "run_tool": "no"
        },
        "qct-parse": {
            "barsDetection": False,
            "evaluateBars": False,
            "contentFilter": [],
            "profile": [],
            "tagname": None,
            "thumbExport": False
        }
    },
    "outputs": {
        "access_file": "no",
        "report": "no",
        "qctools_ext": "qctools.xml.gz"
    },
    "fixity": {
        "check_fixity": "no",
        "validate_stream_fixity": "no",
        "embed_stream_fixity": "no",
        "output_fixity": "no",
        "overwrite_stream_fixity": "no"
    }
}

JPC_AV_SVHS = {
    "Source_VTR": ["SVO5800", "SN 122345", "composite", "analog balanced"], 
    "TBC_Framesync": ["DPS575 with flash firmware h2.16", "SN 15230", "SDI", "audio embedded"], 
    "ADC": ["DPS575 with flash firmware h2.16", "SN 15230", "SDI"], 
    "Capture_Device": ["Black Magic Ultra Jam", "SN B022159", "Thunderbolt"],
    "Computer": ["2023 Mac Mini", "Apple M2 Pro chip", "SN H9HDW53JMV", "OS 14.5", "vrecord v2023-08-07", "ffmpeg"]
}

BVH3100 = {
    "Source_VTR": ["Sony BVH3100", "SN 10525", "composite", "analog balanced"],
    "TBC_Framesync": ["Sony BVH3100", "SN 10525", "composite", "analog balanced"],
    "ADC": ["Leitch DPS575 with flash firmware h2.16", "SN 15230", "SDI", "embedded"],
    "Capture_Device": ["Blackmagic Design UltraStudio 4K Extreme", "SN B022159", "Thunderbolt"],
    "Computer": ["2023 Mac Mini", "Apple M2 Pro chip", "SN H9HDW53JMV", "OS 14.5", "vrecord v2023-08-07", "ffmpeg"]
}

bowser_filename = {
    "Collection": "2012_79",
    "MediaType": "2",
    "ObjectID": r"\d{3}_\d{1}[a-zA-Z]",
    "DigitalGeneration": "PM",
    "FileExtension": "mkv"
}

JPCAV_filename = {
    "Collection": "JPC",
    "MediaType": "AV",
    "ObjectID": r"\d{5}",
    "DigitalGeneration": None,
    "FileExtension": "mkv"
}


def parse_arguments():
    parser = argparse.ArgumentParser(description="Change command_config.yaml to processing profile")
    parser.add_argument("--profile", choices=["step1", "step2"], help="Select processing profile (step1 or step2)")

    args = parser.parse_args()

    selected_profile = None
    if args.profile:
        if args.profile == "step1":
            selected_profile = profile_step1
        elif args.profile == "step2":
            selected_profile = profile_step2

    return selected_profile


# Only execute if this file is run directly, not imported)
if __name__ == "__main__":
    selected_profile = parse_arguments()
    apply_profile(selected_profile)
