import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Union, Optional

### Change yamls to JSON, include in package with default settings
### Have default loading for now - hopefully easy to keep last used settings
## Could involve writing to the JSON?
### Rely on cli config changes - potentially 

# import SpexConfig
# spex_config = SpexConfig()
# Access the width from ffmpeg video stream
#    expected_width = spex_config.ffmpeg_values['video_stream'].width
#    print(f"Expected video width: {expected_width}")


# # Create a config with all defaults
# checks_config = ChecksConfig()

# # Access specific values
# print(checks_config.outputs['qctools_ext'])  # 'qctools.xml.gz'
# print(checks_config.tools['exiftool'].run_tool)  # 'yes'
# print(checks_config.tools['mediaconch']['mediaconch_policy'])  # 'JPC_AV_NTSC_MKV_2024-09-20.xml'

# # Modify a value
# checks_config.tools['exiftool'].run_tool = 'no'
# checks_config.tools['qct-parse'].barsDetection = False

@dataclass
class FilenameValues:
    Collection: str = 'JPC'
    MediaType: str = 'AV'
    ObjectID: str = r'\d{5}'
    FileExtension: str = 'mkv'

@dataclass
class MediainfoGeneralValues:
    file_extension: str = 'mkv'
    format: str = 'Matroska'
    overall_bit_rate_mode: str = 'Variable'

@dataclass
class MediainfoVideoValues:
    format: str = 'FFV1'
    format_settings_gop: str = 'N=1'
    codec_id: str = 'V_MS/VFW/FOURCC / FFV1'
    width: str = '720 pixels'
    height: str = '486 pixels'
    pixel_aspect_ratio: str = '0.900'
    display_aspect_ratio: str = '4:3'
    frame_rate_mode: str = 'Constant'
    frame_rate: str = '29.970'
    standard: str = 'NTSC'
    color_space: str = 'YUV'
    chroma_subsampling: str = '4:2:2'
    bit_depth: str = '10 bits'
    scan_type: str = 'Interlaced'
    scan_order: str = 'Bottom Field First'
    compression_mode: str = 'Lossless'
    color_primaries: str = 'BT.601 NTSC'
    colour_primaries_source: str = 'Container'
    transfer_characteristics: str = 'BT.709'
    transfer_characteristics_source: str = 'Container'
    matrix_coefficients: str = 'BT.601'
    max_slices_count: str = '24'
    error_detection_type: str = 'Per slice'

@dataclass
class MediainfoAudioValues:
    format: List[str] = field(default_factory=lambda: ['FLAC', 'PCM'])
    channels: str = '2 channels'
    sampling_rate: str = '48.0 kHz'
    bit_depth: str = '24 bits'
    compression_mode: str = 'Lossless'

@dataclass
class ExiftoolValues:
    file_type: str = 'MKV'
    file_type_extension: str = 'mkv'
    mime_type: str = 'video/x-matroska'
    video_frame_rate: str = '29.97'
    image_width: str = '720'
    image_height: str = '486'
    video_scan_type: str = 'Interlaced'
    display_width: str = '4'
    display_height: str = '3'
    display_unit: str = 'Display Aspect Ratio'
    codec_id: List[str] = field(default_factory=lambda: ['A_FLAC', 'A_PCM/INT/LIT'])
    audio_channels: str = '2'
    audio_sample_rate: str = '48000'
    audio_bits_per_sample: str = '24'

@dataclass
class FFmpegVideoStream:
    codec_name: str = 'ffv1'
    codec_long_name: str = 'FFmpeg video codec #1'
    codec_type: str = 'video'
    codec_tag_string: str = 'FFV1'
    codec_tag: str = '0x31564646'
    width: str = '720'
    height: str = '486'
    display_aspect_ratio: str = '4:3'
    pix_fmt: str = 'yuv422p10le'
    color_space: str = 'smpte170m'
    color_transfer: str = 'bt709'
    color_primaries: str = 'smpte170m'
    field_order: str = 'bt'
    bits_per_raw_sample: str = '10'

@dataclass
class FFmpegAudioStream:
    codec_name: List[str] = field(default_factory=lambda: ['flac', 'pcm_s24le'])
    codec_long_name: List[str] = field(default_factory=lambda: ['FLAC (Free Lossless Audio Codec)', 'PCM signed 24-bit little-endian'])
    codec_type: str = 'audio'
    codec_tag: str = '0x0000'
    sample_fmt: str = 's32'
    sample_rate: str = '48000'
    channels: str = '2'
    channel_layout: str = 'stereo'
    bits_per_raw_sample: str = '24'

@dataclass
class FFmpegEncoderSettings:
    source_vtr: List[str] = field(default_factory=lambda: ['Sony BVH3100', 'SN 10525', 'composite', 'analog balanced'])
    tbc_framesync: List[str] = field(default_factory=lambda: ['Sony BVH3100', 'SN 10525', 'composite', 'analog balanced'])
    adc: List[str] = field(default_factory=lambda: ['Leitch DPS575 with flash firmware h2.16', 'SN 15230', 'SDI', 'embedded'])
    capture_device: List[str] = field(default_factory=lambda: ['Blackmagic Design UltraStudio 4K Extreme', 'SN B022159', 'Thunderbolt'])
    computer: List[str] = field(default_factory=lambda: ['2023 Mac Mini', 'Apple M2 Pro chip', 'SN H9HDW53JMV', 'OS 14.5', 'vrecord v2023-08-07', 'ffmpeg'])

@dataclass
class FFmpegFormat:
    format_name: str = 'matroska webm'
    format_long_name: str = 'Matroska / WebM'
    tags: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'creation_time': None,
        'ENCODER': None,
        'TITLE': None,
        'ENCODER_SETTINGS': None,
        'DESCRIPTION': None,
        'ORIGINAL MEDIA TYPE': None,
        'ENCODED_BY': None
    })

@dataclass
class SpexConfig:
    filename_values: FilenameValues = field(default_factory=FilenameValues)
    mediainfo_values: Dict[str, Union[MediainfoGeneralValues, MediainfoVideoValues, MediainfoAudioValues]] = field(default_factory=lambda: {
        'expected_general': MediainfoGeneralValues(),
        'expected_video': MediainfoVideoValues(),
        'expected_audio': MediainfoAudioValues()
    })
    exiftool_values: ExiftoolValues = field(default_factory=ExiftoolValues)
    ffmpeg_values: Dict[str, Union[FFmpegVideoStream, FFmpegAudioStream, FFmpegFormat]] = field(default_factory=lambda: {
        'video_stream': FFmpegVideoStream(),
        'audio_stream': FFmpegAudioStream(),
        'format': FFmpegFormat()
    })

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union

@dataclass
class FixityConfig:
    check_fixity: str = 'no'
    check_stream_fixity: str = 'no'
    embed_stream_fixity: str = 'yes'
    output_fixity: str = 'yes'
    overwrite_stream_fixity: str = 'no'

@dataclass
class ToolCheckConfig:
    check_tool: str = 'yes'
    run_tool: str = 'yes'

@dataclass
class QctParseConfig:
    barsDetection: Optional[bool] = True
    evaluateBars: Optional[bool] = True
    contentFilter: Dict[str, str] = field(default_factory=lambda: {'profile': ''})
    tagname: Optional[List[Union[str, int]]] = None
    thumbExport: Optional[bool] = True

@dataclass
class ChecksConfig:
    outputs: Dict[str, str] = field(default_factory=lambda: {
        'access_file': 'no',
        'report': 'no',
        'qctools_ext': 'qctools.xml.gz'
    })
    
    fixity: FixityConfig = field(default_factory=FixityConfig)
    
    tools: Dict[str, Union[ToolCheckConfig, Dict[str, str]]] = field(default_factory=lambda: {
        'exiftool': ToolCheckConfig(check_tool='yes', run_tool='yes'),
        'ffprobe': ToolCheckConfig(check_tool='no', run_tool='yes'),
        'mediaconch': {
            'mediaconch_policy': 'JPC_AV_NTSC_MKV_2024-09-20.xml',
            'run_mediaconch': 'yes'
        },
        'mediainfo': ToolCheckConfig(check_tool='yes', run_tool='yes'),
        'mediatrace': ToolCheckConfig(check_tool='yes', run_tool='yes'),
        'qctools': ToolCheckConfig(check_tool='no', run_tool='no'),
        'qct-parse': QctParseConfig()
    })