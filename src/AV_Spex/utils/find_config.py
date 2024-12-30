import os
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Union, Optional


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
class EncoderSettings:
    Source_VTR: List[str] = field(default_factory=lambda: [
        'Sony BVH3100',
        'SN 10525',
        'composite',
        'analog balanced'
    ])
    TBC_Framesync: List[str] = field(default_factory=lambda: [
        'Sony BVH3100',
        'SN 10525',
        'composite',
        'analog balanced'
    ])
    ADC: List[str] = field(default_factory=lambda: [
        'Leitch DPS575 with flash firmware h2.16',
        'SN 15230',
        'SDI',
        'embedded'
    ])
    Capture_Device: List[str] = field(default_factory=lambda: [
        'Blackmagic Design UltraStudio 4K Extreme',
        'SN B022159',
        'Thunderbolt'
    ])
    Computer: List[str] = field(default_factory=lambda: [
        '2023 Mac Mini',
        'Apple M2 Pro chip',
        'SN H9HDW53JMV',
        'OS 14.5',
        'vrecord v2023-08-07',
        'ffmpeg'
    ])

@dataclass
class MediaTraceValues:
    COLLECTION: Optional[str] = None
    TITLE: Optional[str] = None
    CATALOG_NUMBER: Optional[str] = None
    DESCRIPTION: Optional[str] = None
    DATE_DIGITIZED: Optional[str] = None
    ENCODER_SETTINGS: EncoderSettings = field(default_factory=EncoderSettings)
    ENCODED_BY: Optional[str] = None
    ORIGINAL_MEDIA_TYPE: Optional[str] = None
    DATE_TAGGED: Optional[str] = None
    TERMS_OF_USE: Optional[str] = None
    _TECHNICAL_NOTES: Optional[str] = None
    _ORIGINAL_FPS: Optional[str] = None

@dataclass
class AllBlackContent:
    YMAX: tuple[float, str] = field(default_factory=lambda: (300, 'lt'))
    YHIGH: tuple[float, str] = field(default_factory=lambda: (115, 'lt'))
    YLOW: tuple[float, str] = field(default_factory=lambda: (97, 'lt'))
    YMIN: tuple[float, str] = field(default_factory=lambda: (6.5, 'lt'))

@dataclass
class StaticContent:
    YMIN: tuple[float, str] = field(default_factory=lambda: (5, 'lt'))
    YLOW: tuple[float, str] = field(default_factory=lambda: (6, 'lt'))
    YAVG: tuple[float, str] = field(default_factory=lambda: (240, 'lt'))
    YMAX: tuple[float, str] = field(default_factory=lambda: (1018, 'gt'))
    YDIF: tuple[float, str] = field(default_factory=lambda: (260, 'gt'))
    ULOW: tuple[float, str] = field(default_factory=lambda: (325, 'gt'))
    UAVG: tuple[float, str] = field(default_factory=lambda: (509, 'gt'))
    UHIGH: tuple[float, str] = field(default_factory=lambda: (695, 'lt'))
    UMAX: tuple[float, str] = field(default_factory=lambda: (990, 'gt'))
    UDIF: tuple[float, str] = field(default_factory=lambda: (138, 'gt'))
    VMIN: tuple[float, str] = field(default_factory=lambda: (100, 'lt'))
    VLOW: tuple[float, str] = field(default_factory=lambda: (385, 'gt'))
    VAVG: tuple[float, str] = field(default_factory=lambda: (500, 'gt'))
    VHIGH: tuple[float, str] = field(default_factory=lambda: (650, 'lt'))
    VMAX: tuple[float, str] = field(default_factory=lambda: (940, 'gt'))
    VDIF: tuple[float, str] = field(default_factory=lambda: (98, 'gt'))

@dataclass
class Content:
    allBlack: AllBlackContent = field(default_factory=AllBlackContent)
    static: StaticContent = field(default_factory=StaticContent)

@dataclass
class DefaultProfile:
    YLOW: float = 64
    YHIGH: float = 940
    ULOW: float = 64
    UHIGH: float = 940
    VLOW: float = 0
    VHIGH: float = 1023
    SATMAX: float = 181.02
    TOUT: float = 0.009
    VREP: float = 0.03

@dataclass
class HighToleranceProfile:
    YLOW: float = 40
    YMAX: float = 1000
    UMIN: float = 64
    UMAX: float = 1000
    VMIN: float = 0
    VMAX: float = 1023
    SATMAX: float = 181.02
    TOUT: float = 0.009
    VREP: float = 0.03

@dataclass
class MidToleranceProfile:
    YLOW: float = 40
    YMAX: float = 980
    UMIN: float = 64
    UMAX: float = 980
    VMIN: float = 0
    VMAX: float = 1023
    SATMAX: float = 181.02
    TOUT: float = 0.009
    VREP: float = 0.03

@dataclass
class LowToleranceProfile:
    YLOW: float = 64
    YMAX: float = 940
    UMIN: float = 64
    UMAX: float = 940
    VMIN: float = 0
    VMAX: float = 1023
    SATMAX: float = 181.02
    TOUT: float = 0.009
    VREP: float = 0.03

@dataclass
class Profiles:
    default: DefaultProfile = field(default_factory=DefaultProfile)
    highTolerance: HighToleranceProfile = field(default_factory=HighToleranceProfile)
    midTolerance: MidToleranceProfile = field(default_factory=MidToleranceProfile)
    lowTolerance: LowToleranceProfile = field(default_factory=LowToleranceProfile)

@dataclass
class FullTagList:
    YMIN: Optional[float] = None
    YLOW: Optional[float] = None
    YAVG: Optional[float] = None
    YHIGH: Optional[float] = None
    YMAX: Optional[float] = None
    UMIN: Optional[float] = None
    ULOW: Optional[float] = None
    UAVG: Optional[float] = None
    UHIGH: Optional[float] = None
    UMAX: Optional[float] = None
    VMIN: Optional[float] = None
    VLOW: Optional[float] = None
    VAVG: Optional[float] = None
    VHIGH: Optional[float] = None
    VMAX: Optional[float] = None
    SATMIN: Optional[float] = None
    SATLOW: Optional[float] = None
    SATAVG: Optional[float] = None
    SATHIGH: Optional[float] = None
    SATMAX: Optional[float] = None
    HUEMED: Optional[float] = None
    HUEAVG: Optional[float] = None
    YDIF: Optional[float] = None
    UDIF: Optional[float] = None
    VDIF: Optional[float] = None
    TOUT: Optional[float] = None
    VREP: Optional[float] = None
    BRNG: Optional[float] = None
    mse_y: Optional[float] = None
    mse_u: Optional[float] = None
    mse_v: Optional[float] = None
    mse_avg: Optional[float] = None
    psnr_y: Optional[float] = None
    psnr_u: Optional[float] = None
    psnr_v: Optional[float] = None
    psnr_avg: Optional[float] = None
    Overall_Min_level: Optional[float] = None
    Overall_Max_level: Optional[float] = None

@dataclass
class SmpteColorBars:
    YMAX: float = 940
    YMIN: float = 28
    UMIN: float = 148
    UMAX: float = 876
    VMIN: float = 124
    VMAX: float = 867
    SATMIN: float = 0
    SATMAX: float = 405

@dataclass
class QCTParseValues:
    content: Content = field(default_factory=Content)
    profiles: Profiles = field(default_factory=Profiles)
    fullTagList: FullTagList = field(default_factory=FullTagList)
    smpte_color_bars: SmpteColorBars = field(default_factory=SmpteColorBars)


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
    mediatrace_values: MediaTraceValues = field(default_factory=MediaTraceValues)
    qct_parse_values: QCTParseValues = field(default_factory=QCTParseValues)

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
    pass
