#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import pandas as pd
import plotly.graph_objs as go
from ..utils.log_setup import logger
from ..utils.find_config import config_path


# Read CSV files and convert them to HTML tables
def csv_to_html_table(csv_file, style_mismatched=False, mismatch_color="#ff9999", match_color="#d2ffed", check_fail=False):
    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    table_html = '<table>\n'
    header = rows[0]
    table_html += '  <tr>\n'
    for cell in header:
        table_html += f'    <th>{cell}</th>\n'
    table_html += '  </tr>\n'
    
    for row in rows[1:]:
        table_html += '  <tr>\n'
        for i, cell in enumerate(row):
            if check_fail and cell.lower() == "fail":
                table_html += f'    <td style="background-color: {mismatch_color};">{cell}</td>\n'
            elif check_fail and cell.lower() == "pass":
                table_html += f'    <td style="background-color: {match_color};">{cell}</td>\n'
            elif style_mismatched and i == 2 and row[2] != '' and row[1] != row[2]:
                table_html += f'    <td style="background-color: {match_color};">{cell}</td>\n'
            elif style_mismatched and i == 3 and row[2] != '' and row[1] != row[2]:
                table_html += f'    <td style="background-color: {mismatch_color};">{cell}</td>\n'
            else:
                table_html += f'    <td>{cell}</td>\n'
        table_html += '  </tr>\n'
    table_html += '</table>\n'
    return table_html

def read_text_file(text_file_path):
    with open(text_file_path, 'r') as file:
        return file.read()
    
def prepare_file_section(file_path, process_function=None):
    if file_path:
        if process_function:
            file_content = process_function(file_path)
        else:
            file_content = read_text_file(file_path)
        file_name = os.path.basename(file_path)
    else:
        file_content = ''
        file_name = ''
    return file_content, file_name

import os

def parse_timestamp(timestamp_str):
    if not timestamp_str:
        return (9999, 99, 99, 99, 9999)  # Return a placeholder tuple for non-timestamp entries
    # Convert timestamp to a tuple of integers
    timestamp_tuple = tuple(map(int, timestamp_str.split(':')))
    return timestamp_tuple

def parse_profile(profile_name):
    # Define a custom order for the profile names
    profile_order = {
        "color_bars_detection": 0,
        "color_bars_evaluation": 1,
        "threshold_profile": 2,  # Assuming all threshold_profile_* come together
        "tag_check": 3
    }
    
    for key in profile_order:
        if profile_name.startswith(key):
            return profile_order[key]
    return 99  # Default order if profile_name does not match any known profiles

def find_qct_thumbs(report_directory):
    thumbs_dict = {}
    thumb_exports_dir = os.path.join(report_directory, 'ThumbExports')
    
    if os.path.isdir(thumb_exports_dir):
        for file in os.listdir(thumb_exports_dir):
            file_path = os.path.join(thumb_exports_dir, file)
            if os.path.isfile(file_path) and not file.startswith('.DS_Store'):
                qct_thumb_path = file_path
                filename_segments = file.split('.')
                if len(filename_segments) >= 5:
                    profile_name = filename_segments[1]
                    tag_name = filename_segments[2]
                    tag_value = filename_segments[3]
                    timestamp_as_list = filename_segments[4:-1]
                    timestamp_as_string = ':'.join(timestamp_as_list)
                    if profile_name == 'color_bars_detection':
                        qct_thumb_name = f'First frame of color bars\n\nAt timecode: {timestamp_as_string}'
                    else:
                        qct_thumb_name = f'Failed frame \n\nQCTools check: {profile_name} \n\nQCTools tag: {tag_name} \n\nValue: {tag_value} at {timestamp_as_string}'
                    thumbs_dict[qct_thumb_name] = (qct_thumb_path, profile_name, timestamp_as_string)
                else:
                    qct_thumb_name = ':'.join(filename_segments)
                    thumbs_dict[qct_thumb_name] = (qct_thumb_path, "", "")

    # Sort thumbs_dict by timestamp if possible
    sorted_thumbs_dict = {}
    for key in sorted(thumbs_dict.keys(), key=lambda x: (parse_profile(thumbs_dict[x][1]), parse_timestamp(thumbs_dict[x][2]))):
        sorted_thumbs_dict[key] = thumbs_dict[key][0]

    return sorted_thumbs_dict

def find_report_csvs(report_directory):

    qctools_colorbars_duration_output = None
    qctools_bars_eval_check_output = None
    qctools_bars_eval_timestamps = None
    colorbars_values_output = None
    qctools_content_check_output = None
    qctools_profile_check_output = None
    qctools_profile_timestamps = None
    difference_csv = None

    if os.path.isdir(report_directory):
        for file in os.listdir(report_directory):
            file_path = os.path.join(report_directory, file)
            if os.path.isfile(file_path) and not file.startswith('.DS_Store'):
                if file.startswith("qct-parse_"):
                    if "qct-parse_colorbars_durations" in file:
                        qctools_colorbars_duration_output = file_path
                    elif "qct-parse_colorbars_eval_summary" in file:
                        qctools_bars_eval_check_output = file_path
                    elif "qct-parse_colorbars_eval_timestamps" in file:
                        qctools_bars_eval_timestamps = file_path
                    elif "qct-parse_colorbars_values" in file:
                        colorbars_values_output = file_path
                    elif "qct-parse_contentFilter_summary" in file:
                        qctools_content_check_output = file_path
                    elif "qct-parse_profile_summary" in file:
                        qctools_profile_check_output = file_path
                    elif "qct-parse_profile_timestamps" in file:
                        qctools_profile_timestamps = file_path
                elif "metadata_difference" in file:
                    difference_csv = file_path

    return qctools_colorbars_duration_output, qctools_bars_eval_check_output, qctools_bars_eval_timestamps, colorbars_values_output, qctools_content_check_output, qctools_profile_check_output, qctools_profile_timestamps, difference_csv

def find_qc_metadata(destination_directory):

    exiftool_output_path = None 
    ffprobe_output_path = None
    mediainfo_output_path = None
    mediaconch_csv = None

    if os.path.isdir(destination_directory):
        for file in os.listdir(destination_directory):
            file_path = os.path.join(destination_directory, file)
            if os.path.isfile(file_path) and not file.startswith('.DS_Store'):
                if "_exiftool_output" in file:
                    exiftool_output_path = file_path
                if "_ffprobe_output" in file:
                    ffprobe_output_path = file_path
                if "_mediinfo_output" in file:
                    mediainfo_output_path = file_path
                if "_mediaconch_output" in file:
                    mediaconch_csv = file_path

    return exiftool_output_path,ffprobe_output_path,mediainfo_output_path,mediaconch_csv

def make_color_bars_graphs(video_id, qctools_colorbars_duration_output, colorbars_values_output):

    # Read the CSV files
    colorbars_df = pd.read_csv(colorbars_values_output)

    # Read the colorbars duration CSV
    with open(qctools_colorbars_duration_output, 'r') as file:
        duration_lines = file.readlines()
        duration_text = duration_lines[1].strip()  # The 2nd line contains the color bars duration
        
    duration_text = duration_text.replace(',',' - ')
    duration_text = "Colorbars duration: " + duration_text

    # Create the bar chart for the colorbars values
    colorbars_fig = go.Figure(data=[
        go.Bar(name='SMPTE Colorbars', x=colorbars_df['QCTools Fields'], y=colorbars_df['SMPTE Colorbars'], marker=dict(color='#378d6a')),
        go.Bar(name=f'{video_id} Colorbars', x=colorbars_df['QCTools Fields'], y=colorbars_df[f'{video_id} Colorbars'], marker=dict(color='#bf971b'))
    ])
    colorbars_fig.update_layout(barmode='group', title=f'SMPTE Colorbars vs {video_id} Colorbars')

    # Save each chart as an HTML string
    colorbars_barchart_html = colorbars_fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Create the complete HTML with the duration text added
    colorbars_html = f'''
    <div>
        <p>{duration_text}</p>
        {colorbars_barchart_html}
    </div>
    '''

    return colorbars_html
    
def make_profile_piecharts(qctools_profile_check_output,qctools_profile_timestamps):

    # Read the profile summary CSV, skipping the first two metadata lines
    profile_summary_df = pd.read_csv(qctools_profile_check_output, skiprows=3)

    # Extract the total frames from the third line of the profile summary file
    with open(qctools_profile_check_output, 'r') as file:
        lines = file.readlines()
        total_frames_line = lines[2].strip()  # The third line (index 2) contains TotalFrames

    # Parse the total frames line
    _, total_frames = total_frames_line.split(',')
    total_frames = int(total_frames)

    # Read the timestamps CSV, skipping the header row
    timestamps_df = pd.read_csv(qctools_profile_timestamps)
    timestamps = timestamps_df.iloc[:, 0].tolist()  # Extract the first column as a list
    
    # Replace ',' with ' - ' for each timestamp
    formatted_timestamps = [timestamp.replace(',', ' - ').strip().strip('"') for timestamp in timestamps]

    # Format the timestamps for HTML
    formatted_timestamps_html = '<br>'.join(formatted_timestamps)
    
    # Create pie charts for the profile summary
    profile_summary_pie_charts = []
    for index, row in profile_summary_df.iterrows():
        tag = row['Tag']
        failed_frames = int(row['Number of failed frames'])
        percentage = float(row['Percentage of failed frames'])
        if tag != 'Total' and percentage > 0:
            pie_fig = go.Figure(data=[go.Pie(labels=['Failed Frames', 'Other Frames'],
                                            values=[failed_frames, total_frames - failed_frames],
                                            hole=.3,
                                            marker=dict(colors=['#ffbaba', '#d2ffed']))])
            pie_fig.update_layout(title=f"{tag} - {percentage:.2f}% ({failed_frames} frames)", height=400, width=400,
                                  paper_bgcolor='#f5e9e3')
            profile_summary_pie_charts.append(pie_fig.to_html(full_html=False, include_plotlyjs=False))

    # Arrange pie charts horizontally
    profile_piecharts_html = ''.join(
        f'<div style="display:inline-block; margin-right: 10px;">{pie_chart}</div>'
        for pie_chart in profile_summary_pie_charts
    )

    profile_summary_html = f'''
    <div>
        <p>Times stamps of frames with at least one fail during qct-parse profile check</p>
        <p>{formatted_timestamps_html}</p>
        {profile_piecharts_html}
    </div>
    '''

    return profile_summary_html

def write_html_report(video_id,report_directory,destination_directory,html_report_path):

    qctools_colorbars_duration_output, qctools_bars_eval_check_output, qctools_bars_eval_timestamps, colorbars_values_output, qctools_content_check_output, qctools_profile_check_output, qctools_profile_timestamps, difference_csv = find_report_csvs(report_directory)
    
    exiftool_output_path,mediainfo_output_path,ffprobe_output_path,mediaconch_csv = find_qc_metadata(destination_directory)
    
    # Initialize and create html from 
    mc_csv_html, mediaconch_csv_filename = prepare_file_section(mediaconch_csv, lambda path: csv_to_html_table(path, style_mismatched=False, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=True))
    diff_csv_html, difference_csv_filename = prepare_file_section(difference_csv, lambda path: csv_to_html_table(path, style_mismatched=True, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=False))
    exif_file_content, exif_file_filename = prepare_file_section(exiftool_output_path)
    mi_file_content, mi_file_filename = prepare_file_section(mediainfo_output_path)
    ffprobe_file_content, ffprobe_file_filename = prepare_file_section(ffprobe_output_path)

    # Create graphs for all existing csv files
    if colorbars_values_output:
        colorbars_html = make_color_bars_graphs(video_id,qctools_colorbars_duration_output,colorbars_values_output)
    else:
         colorbars_html = None
    if qctools_profile_check_output:
        profile_summary_html = make_profile_piecharts(qctools_profile_check_output,qctools_profile_timestamps)
    else:
        profile_summary_html = None
    
    # Get the absolute path of the script file
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Determine the  path to the image file
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
    logo_image_path = os.path.join(root_dir, 'av_spex_the_logo.png')
    eq_image_path = os.path.join(root_dir, 'germfree_eq.png')

    # Get qct-parse thumbs if they exists
    thumbs_dict = find_qct_thumbs(report_directory)

    # HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AV Spex Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #fcfdff;
                color: #011054;
                margin: 30px;
            }}
            h1 {{
                font-size: 24px;
                text-align: center;
                margin-top: 20px;
                color: #378d6a;
            }}
            h2 {{
                font-size: 20px;
                font-weight: bold;
                margin-top: 30px;
                color: #0a5f1c;
                text-decoration: underline;
            }}
            h3 {{
                font-size: 18px;
                margin-top: 20px;
                color: #bf971b;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                margin-bottom: 20px;
                border: 2px solid #4d2b12;
            }}
            th, td {{
                border: 1.5px solid #4d2b12;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #fbe4eb;
                font-weight: bold;
            }}
            pre {{
                background-color: #f5e9e3;
                border: 1px solid #4d2b12;
                padding: 10px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
        <img src="{logo_image_path}" alt="AV Spex Logo" style="display: block; margin-left: auto; margin-right: auto; width: 25%; margin-top: 20px;">
    </head>
    <body>
        <h1>AV Spex Report</h1>
        <h2>{video_id}</h2>
        <img src="{eq_image_path}" alt="AV Spex Graphic EQ Logo" style="width: 10%">
    """

    if mediaconch_csv:
        html_template += f"""
        <h3>{mediaconch_csv_filename}</h3>
        {mc_csv_html}
        """

    if difference_csv:
        html_template += f"""
        <h3>{difference_csv_filename}</h3>
        {diff_csv_html}
        """

    if thumbs_dict:
        html_template += f"<h3>qct-parse thumbnails</h3>"
        html_template += '<table><tr>'
        for thumb_name, thumb_path in thumbs_dict.items():
            thumb_name_with_breaks = thumb_name.replace("\n", "<br>")
            html_template += f"""
            <td style="text-align: center;">
                <img src="{thumb_path}" alt="{thumb_name}" style="max-width: 175; max-height: 175px; object-fit: contain;">
                <p>{thumb_name_with_breaks}</p>
            </td>
            """
        html_template += '</tr></table>'
    
    if colorbars_html:
        html_template += f"""
        <h3>Colorbars comparison</h3>
        {colorbars_html}
        """

    if profile_summary_html:
        html_template += f"""
        <h3>qct-parse Profile Summary</h3>
        <div style="white-space: nowrap;">
            {profile_summary_html}
        </div>
        """
    
    if exiftool_output_path:
        html_template += f"""
        <h3>{exif_file_filename}</h3>
        <pre>{exif_file_content}</pre>
        """
    
    if mediainfo_output_path:
        html_template += f"""
        <h3>{mi_file_filename}</h3>
        <pre>{mi_file_content}</pre>
        """

    if ffprobe_output_path:
        html_template += f"""
        <h3>{ffprobe_file_filename}</h3>
        <pre>{ffprobe_file_content}</pre>
        """

    html_template += """
    </body>
    </html>
    """

    # Write the HTML file
    with open(html_report_path, 'w') as f:
        f.write(html_template)

    logger.info("\nHTML report generated successfully!")
