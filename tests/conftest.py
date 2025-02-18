# tests/conftest.py
import pytest
import os
import logging
from pathlib import Path

@pytest.fixture
def sample_colorbars_csv(tmp_path):
    """Create a sample colorbars values CSV file"""
    csv_content = """QCTools Fields,SMPTE Colorbars,JPC_AV_05000 Colorbars
YMAX,940.0,1019
YMIN,28.0,4
UMIN,148.0,4
UMAX,876.0,1019
VMIN,124.0,6
VMAX,867.0,1016
SATMIN,0.0,1
SATMAX,405.0,704"""
    
    csv_path = tmp_path / "colorbars_values.csv"
    csv_path.write_text(csv_content)
    return str(csv_path)

@pytest.fixture
def sample_duration_csv(tmp_path):
    """Create a sample duration CSV file"""
    csv_content = """qct-parse color bars found:
00:00:03:1030,00:00:07:12:3320"""
    
    csv_path = tmp_path / "colorbars_duration.csv"
    csv_path.write_text(csv_content)
    return str(csv_path)

@pytest.fixture
def sample_thumbs_dict(tmp_path):
    """Create a sample thumbs dictionary with test image"""
    thumb_dir = tmp_path / "ThumbExports"
    thumb_dir.mkdir()
    test_image = thumb_dir / "JPC_AV_05000.color_bars_detection.bars_found.first_frame.00.00.03.1030.png"
    test_image.write_text("dummy image content")
    
    return {
        'First frame of color bars\n\nAt timecode: 00:00:03:1030': (
            str(test_image),
            'bars_found',
            '00:00:03:1030'
        )
    }

@pytest.fixture
def setup_logging():
    """Setup basic logging configuration for tests"""
    logging.basicConfig(level=logging.CRITICAL)