# tests/test_color_bars.py
import pytest
import os
from AV_Spex.utils.generate_report import make_color_bars_graphs

def test_make_color_bars_graphs_success(sample_colorbars_csv, sample_duration_csv, 
                                      sample_thumbs_dict, setup_logging):
    """Test successful generation of color bars graphs"""
    video_id = "JPC_AV_05000"
    html_output = make_color_bars_graphs(
        video_id,
        sample_duration_csv,
        sample_colorbars_csv,
        sample_thumbs_dict
    )
    
    assert html_output is not None
    assert "Colorbars duration: 00:00:03:1030 - 00:00:07:12:3320" in html_output
    assert 'display: flex;' in html_output
    assert video_id in html_output
    assert "SMPTE Colorbars" in html_output

def test_make_color_bars_graphs_missing_duration_file(sample_colorbars_csv, 
                                                     sample_thumbs_dict, setup_logging):
    """Test behavior when duration file is missing"""
    html_output = make_color_bars_graphs(
        "JPC_AV_05000",
        "nonexistent_file.csv",
        sample_colorbars_csv,
        sample_thumbs_dict
    )
    assert html_output is None

def test_make_color_bars_graphs_empty_duration_file(sample_colorbars_csv, tmp_path, 
                                                   sample_thumbs_dict, setup_logging):
    """Test behavior with empty duration file"""
    empty_duration_file = tmp_path / "empty_duration.csv"
    empty_duration_file.write_text("")
    
    html_output = make_color_bars_graphs(
        "JPC_AV_05000",
        str(empty_duration_file),
        sample_colorbars_csv,
        sample_thumbs_dict
    )
    assert html_output is None

def test_make_color_bars_graphs_no_matching_thumbnail(sample_colorbars_csv, 
                                                     sample_duration_csv, setup_logging):
    """Test behavior when no matching thumbnail is found"""
    empty_thumbs_dict = {
        'Failed frame \n\nSATMAX:705\n\n0:00:00:11:8120': (
            'path/to/other/thumb.png',
            'SATMAX',
            '0:00:00:11:8120'
        )
    }
    
    html_output = make_color_bars_graphs(
        "JPC_AV_05000",
        sample_duration_csv,
        sample_colorbars_csv,
        empty_thumbs_dict
    )
    
    assert html_output is not None
    assert 'bars_found.first_frame' not in html_output