import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional

@dataclass
class FilenameValues:
    Collection: str
    MediaType: str
    ObjectID: str
    FileExtension: str
    DigitalGeneration: Optional[str] = None

@dataclass
class MediainfoGeneralValues:
    file_extension: str
    format: str
    overall_bit_rate_mode: str

@dataclass
class MediainfoVideoValues:
    format: str
    format_settings_gop: str
    codec_id: str
    width: str
    height: str
    pixel_aspect_ratio: str
    display_aspect_ratio: str
    frame_rate_mode: str
    frame_rate: str
    standard: str
    color_space: str
    chroma_subsampling: str
    bit_depth: str
    scan_type: str
    scan_order: str
    compression_mode: str
    color_primaries: str
    colour_primaries_source: str
    transfer_characteristics: str
    transfer_characteristics_source: str
    matrix_coefficients: str
    max_slices_count: str
    error_detection_type: str

@dataclass
class MediainfoAudioValues:
    format: List[str]
    channels: str
    sampling_rate: str
    bit_depth: str
    compression_mode: str

@dataclass
class ExiftoolValues:
    file_type: str
    file_type_extension: str
    mime_type: str
    video_frame_rate: str
    image_width: str
    image_height: str
    video_scan_type: str
    display_width: str
    display_height: str
    display_unit: str
    codec_id: List[str]
    audio_channels: str
    audio_sample_rate: str
    audio_bits_per_sample: str

@dataclass
class FFmpegVideoStream:
    codec_name: str
    codec_long_name: str
    codec_type: str
    codec_tag_string: str
    codec_tag: str
    width: str
    height: str
    display_aspect_ratio: str
    pix_fmt: str
    color_space: str
    color_transfer: str
    color_primaries: str
    field_order: str
    bits_per_raw_sample: str

@dataclass
class FFmpegAudioStream:
    codec_name: List[str]
    codec_long_name: List[str]
    codec_type: str
    codec_tag: str
    sample_fmt: str
    sample_rate: str
    channels: str
    channel_layout: str
    bits_per_raw_sample: str

@dataclass
class FFmpegFormat:
    format_name: str
    format_long_name: str
    tags: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'creation_time': None,
        'ENCODER': None,
        'TITLE': None,
        'ENCODER_SETTINGS': EncoderSettings,
        'DESCRIPTION': None,
        'ORIGINAL MEDIA TYPE': None,
        'ENCODED_BY': None
    })

@dataclass
class EncoderSettings:
    Source_VTR: List[str] = field(default_factory=list)
    TBC_Framesync: List[str] = field(default_factory=list)
    ADC: List[str] = field(default_factory=list)
    Capture_Device: List[str] = field(default_factory=list)
    Computer: List[str] = field(default_factory=list)

@dataclass
class MediaTraceValues:
    COLLECTION: Optional[str]
    TITLE: Optional[str]
    CATALOG_NUMBER: Optional[str]
    DESCRIPTION: Optional[str]
    DATE_DIGITIZED: Optional[str]
    ENCODER_SETTINGS: EncoderSettings
    ENCODED_BY: Optional[str]
    ORIGINAL_MEDIA_TYPE: Optional[str]
    DATE_TAGGED: Optional[str]
    TERMS_OF_USE: Optional[str]
    _TECHNICAL_NOTES: Optional[str]
    _ORIGINAL_FPS: Optional[str]

@dataclass
class AllBlackContent:
    YMAX: tuple[float, str]
    YHIGH: tuple[float, str]
    YLOW: tuple[float, str]
    YMIN: tuple[float, str]

@dataclass
class StaticContent:
    YMIN: tuple[float, str]
    YLOW: tuple[float, str]
    YAVG: tuple[float, str]
    YMAX: tuple[float, str]
    YDIF: tuple[float, str]
    ULOW: tuple[float, str]
    UAVG: tuple[float, str]
    UHIGH: tuple[float, str]
    UMAX: tuple[float, str]
    UDIF: tuple[float, str]
    VMIN: tuple[float, str]
    VLOW: tuple[float, str]
    VAVG: tuple[float, str]
    VHIGH: tuple[float, str]
    VMAX: tuple[float, str]
    VDIF: tuple[float, str]

@dataclass
class Content:
    allBlack: AllBlackContent
    static: StaticContent

@dataclass
class DefaultProfile:
    YLOW: float
    YHIGH: float
    ULOW: float
    UHIGH: float
    VLOW: float
    VHIGH: float
    SATMAX: float
    TOUT: float
    VREP: float

@dataclass
class HighToleranceProfile:
    YLOW: float
    YMAX: float
    UMIN: float
    UMAX: float
    VMIN: float
    VMAX: float
    SATMAX: float
    TOUT: float
    VREP: float

@dataclass
class MidToleranceProfile:
    YLOW: float
    YMAX: float
    UMIN: float
    UMAX: float
    VMIN: float
    VMAX: float
    SATMAX: float
    TOUT: float
    VREP: float

@dataclass
class LowToleranceProfile:
    YLOW: float
    YMAX: float
    UMIN: float
    UMAX: float
    VMIN: float
    VMAX: float
    SATMAX: float
    TOUT: float
    VREP: float

@dataclass
class Profiles:
    default: DefaultProfile
    highTolerance: HighToleranceProfile
    midTolerance: MidToleranceProfile
    lowTolerance: LowToleranceProfile

@dataclass
class FullTagList:
    YMIN: Optional[float]
    YLOW: Optional[float]
    YAVG: Optional[float]
    YHIGH: Optional[float]
    YMAX: Optional[float]
    UMIN: Optional[float]
    ULOW: Optional[float]
    UAVG: Optional[float]
    UHIGH: Optional[float]
    UMAX: Optional[float]
    VMIN: Optional[float]
    VLOW: Optional[float]
    VAVG: Optional[float]
    VHIGH: Optional[float]
    VMAX: Optional[float]
    SATMIN: Optional[float]
    SATLOW: Optional[float]
    SATAVG: Optional[float]
    SATHIGH: Optional[float]
    SATMAX: Optional[float]
    HUEMED: Optional[float]
    HUEAVG: Optional[float]
    YDIF: Optional[float]
    UDIF: Optional[float]
    VDIF: Optional[float]
    TOUT: Optional[float]
    VREP: Optional[float]
    BRNG: Optional[float]
    mse_y: Optional[float]
    mse_u: Optional[float]
    mse_v: Optional[float]
    mse_avg: Optional[float]
    psnr_y: Optional[float]
    psnr_u: Optional[float]
    psnr_v: Optional[float]
    psnr_avg: Optional[float]
    Overall_Min_level: Optional[float]
    Overall_Max_level: Optional[float]

@dataclass
class SmpteColorBars:
    YMAX: float
    YMIN: float
    UMIN: float
    UMAX: float
    VMIN: float
    VMAX: float
    SATMIN: float
    SATMAX: float

@dataclass
class QCTParseValues:
    content: Content
    profiles: Profiles
    fullTagList: FullTagList
    smpte_color_bars: SmpteColorBars

@dataclass
class SpexConfig:
    filename_values: FilenameValues
    mediainfo_values: Dict[str, Union[MediainfoGeneralValues, MediainfoVideoValues, MediainfoAudioValues]]
    exiftool_values: ExiftoolValues
    ffmpeg_values: Dict[str, Union[FFmpegVideoStream, FFmpegAudioStream, FFmpegFormat]]
    mediatrace_values: MediaTraceValues
    qct_parse_values: QCTParseValues

# Output configuration
@dataclass
class OutputsConfig:
    access_file: str
    report: str
    qctools_ext: str

# Fixity configuration
@dataclass
class FixityConfig:
    check_fixity: str
    validate_stream_fixity: str
    embed_stream_fixity: str
    output_fixity: str
    overwrite_stream_fixity: str

# Tool-specific configurations
@dataclass
class BasicToolConfig:
    check_tool: str
    run_tool: str

@dataclass
class QCToolsConfig:
    run_tool: str

@dataclass
class MediaConchConfig:
    mediaconch_policy: str
    run_mediaconch: str

@dataclass
class QCTParseToolConfig:
    run_tool: str
    barsDetection: bool
    evaluateBars: bool
    contentFilter: List[str]
    profile: List[str]
    tagname: Optional[str]
    thumbExport: bool

@dataclass
class ToolsConfig:
    exiftool: BasicToolConfig
    ffprobe: BasicToolConfig
    mediaconch: MediaConchConfig
    mediainfo: BasicToolConfig
    mediatrace: BasicToolConfig
    qctools: QCToolsConfig
    qct_parse: QCTParseToolConfig

@dataclass
class ChecksConfig:
    outputs: OutputsConfig
    fixity: FixityConfig
    tools: ToolsConfig