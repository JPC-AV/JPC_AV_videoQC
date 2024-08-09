#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
os.environ["NUMEXPR_MAX_THREADS"] = "11"  #troubleshooting goofy numbpy related error "Note: NumExpr detected 11 cores but "NUMEXPR_MAX_THREADS" not set, so enforcing safe limit of 8.
# NumExpr defaulting to 8 threads."
import pandas as pd
import plotly.graph_objs as go
from base64 import b64encode
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
        "threshold_profile": 2, 
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
                        qct_thumb_name = f'Failed frame \n\n{tag_name}:{tag_value}\n\n{timestamp_as_string}'
                    thumbs_dict[qct_thumb_name] = (qct_thumb_path, tag_name, timestamp_as_string)
                else:
                    qct_thumb_name = ':'.join(filename_segments)
                    thumbs_dict[qct_thumb_name] = (qct_thumb_path, "", "")

    # Sort thumbs_dict by timestamp if possible
    sorted_thumbs_dict = {}
    for key in sorted(thumbs_dict.keys(), key=lambda x: (parse_profile(thumbs_dict[x][1]), parse_timestamp(thumbs_dict[x][2]))):
        sorted_thumbs_dict[key] = thumbs_dict[key]

    return sorted_thumbs_dict

def find_report_csvs(report_directory):

    qctools_colorbars_duration_output = None
    qctools_bars_eval_check_output = None
    qctools_bars_eval_timestamps = None
    colorbars_values_output = None
    # consider making qctools_content_check_output a list, and appending to support multiple content summaries 
    # could potentially make check for qctools_content_check_output diff than others though
    qctools_content_check_outputs = []
    qctools_profile_check_output = None
    qctools_profile_timestamps = None
    profile_fails_csv = None
    tag_fails_csv = None
    colorbars_eval_fails_csv = None
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
                    elif "qct-parse_colorbars_values" in file:
                        colorbars_values_output = file_path
                    elif "qct-parse_contentFilter" in file:
                        qctools_content_check_outputs.append(file_path)
                    elif "qct-parse_profile_summary" in file:
                        qctools_profile_check_output = file_path
                    elif "qct-parse_profile_failures" in file:
                        profile_fails_csv = file
                    elif "qct-parse_tags_failures" in file:
                        tag_fails_csv = file
                    elif "qct-parse_colorbars_eval_failures" in file:
                        colorbars_eval_fails_csv = file
                elif "metadata_difference" in file:
                    difference_csv = file_path


    return qctools_colorbars_duration_output, qctools_bars_eval_check_output, colorbars_values_output, qctools_content_check_outputs, qctools_profile_check_output, profile_fails_csv, tag_fails_csv, colorbars_eval_fails_csv, difference_csv

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
                if "_mediainfo_output" in file:
                    mediainfo_output_path = file_path
                if "_mediaconch_output" in file:
                    mediaconch_csv = file_path

    return exiftool_output_path,ffprobe_output_path,mediainfo_output_path,mediaconch_csv

def summarize_failures(failure_csv_path):  # Change parameter to accept CSV file path
    """
    Summarizes the failure information from the CSV file, prioritizing tags 
    with the greatest difference between tag value and threshold.

    Args:
        failure_csv_path (str): The path to the CSV file containing failure details.

    Returns:
        str: A formatted summary of the failures.
    """
    failureInfo = {}
    # 0. Read the failure information from the CSV
    with open(failure_csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            timestamp = row['Timestamp']
            if timestamp not in failureInfo:
                failureInfo[timestamp] = []
            failureInfo[timestamp].append({
                'tag': row['Tag'],
                'tagValue': float(row['Tag Value']),  # Convert to float
                'over': float(row['Threshold'])     # Convert to float
            })
    
    # 1. Collect all unique tags and count their occurrences
    tag_counts = {}
    for info_list in failureInfo.values():
        for info in info_list:
            tag = info['tag']
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # 2. Determine the maximum number of frames per tag
    num_tags = len(tag_counts)
    max_frames_per_tag = 5 if num_tags <= 2 else 3

    # 3. Flatten the failureInfo dictionary into a list of tuples
    all_failures = []
    for timestamp, info_list in failureInfo.items():
        for info in info_list:
            all_failures.append((timestamp, info))  # Store as (timestamp, info) tuples

    # 4. Sort the flattened list based on tag value difference
    all_failures.sort(key=lambda x: abs(x[1]['tagValue'] - x[1]['over']), reverse=True)

    # 5. Limit the number of frames per tag
    limited_failures = []
    tag_counts = {tag: 0 for tag in tag_counts}  # Reset tag counts
    for timestamp, info in all_failures:
        tag = info['tag']
        if tag_counts[tag] < max_frames_per_tag:
            limited_failures.append((timestamp, info))
            tag_counts[tag] += 1

    # 6. Group the limited failures back into a dictionary by timestamp
    summary_dict = {}
    for timestamp, info in limited_failures:
        if timestamp not in summary_dict:
            summary_dict[timestamp] = []
        summary_dict[timestamp].append(info)

    return summary_dict

def make_color_bars_graphs(video_id, qctools_colorbars_duration_output, colorbars_values_output, sorted_thumbs_dict):

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
    colorbars_fig.update_layout(barmode='group')

    # Save each chart as an HTML string
    colorbars_barchart_html = colorbars_fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Add annotations for the thumbnail
    thumbnail_html = ''
    for thumb_name, (thumb_path, profile_name, timestamp) in sorted_thumbs_dict.items():
        if "bars_found.first_frame" in thumb_path:
            thumb_name_with_breaks = thumb_name.replace("\n", "<br>")
            thumbnail_html = f'''
                <img src="{thumb_path}" alt="{thumb_name}" style="width:200px; height:auto;">
                <p>{thumb_name_with_breaks}</p>
            '''
            break
    
    # Create the complete HTML with the duration text and the thumbnail/barchart side-by-side
    colorbars_html = f'''
    <div style="display: flex; align-items: center; justify-content: center; background-color: #f5e9e3; padding: 10px;">
        <div>
            {thumbnail_html}
            <p>{duration_text}</p>
        </div>
        <div style="margin-left: 20px;">  
            {colorbars_barchart_html}
        </div>
    </div>
    '''

    return colorbars_html
    
def make_profile_piecharts(qctools_profile_check_output,sorted_thumbs_dict,failureInfoSummary):

    # Read the profile summary CSV, skipping the first two metadata lines
    profile_summary_df = pd.read_csv(qctools_profile_check_output, skiprows=3)

    # Extract the total frames from the third line of the profile summary file
    with open(qctools_profile_check_output, 'r') as file:
        lines = file.readlines()
        total_frames_line = lines[2].strip()  # The third line (index 2) contains TotalFrames

    # Parse the total frames line
    _, total_frames = total_frames_line.split(',')
    total_frames = int(total_frames)
    
    # Create pie charts for the profile summary
    profile_summary_pie_charts = []
    for index, row in profile_summary_df.iterrows():
        tag = row['Tag']
        failed_frames = int(row['Number of failed frames'])
        percentage = float(row['Percentage of failed frames'])

        if tag != 'Total' and percentage > 0:
            # Initialize variables for summary data
            failed_frame_timestamps = []
            failed_frame_values = []
            failed_frame_thresholds = []  # New list to store thresholds

            # Get failure details for this tag
            for timestamp, info_list in failureInfoSummary.items():
                for info in info_list:
                    if info['tag'] == tag:
                        failed_frame_timestamps.append(timestamp)
                        failed_frame_values.append(info['tagValue'])
                        failed_frame_thresholds.append(info['over'])  # Store thresholds
            
            # Create formatted failure summary string
            formatted_failures = "<br>".join(
                f"<b>Timestamp: {timestamp}</b><br><b>Value:</b> {value}<br><b>Threshold:</b> {threshold}<br>" 
                for timestamp, value, threshold in zip(failed_frame_timestamps, failed_frame_values, failed_frame_thresholds)
            )
            summary_html = f"""
            <div style="display: flex; flex-direction: column; align-items: center; background-color: #f5e9e3; padding: 10px;">
                <p><b>Peak Values outside of Threshold for {tag}:</b></p>
                <p>{formatted_failures}</p>
            </div>
            """

            # Generate Pie chart
            pie_fig = go.Figure(data=[go.Pie(
                labels=['Failed Frames', 'Other Frames'],
                values=[failed_frames, total_frames - failed_frames],
                hole=.3,
                marker=dict(colors=['#ffbaba', '#d2ffed'])
            )])
            pie_fig.update_layout(title=f"{tag} - {percentage:.2f}% ({failed_frames} frames)", height=400, width=400,
                                paper_bgcolor='#f5e9e3')

            # Get Thumbnails
            thumbnail_html = ''
            for thumb_name, (thumb_path, profile_name, timestamp) in sorted_thumbs_dict.items():
                if profile_name == tag:
                    thumb_name_with_breaks = thumb_name.replace("\n", "<br>")
                    with open(thumb_path, "rb") as image_file:
                        encoded_string = b64encode(image_file.read()).decode()
                    thumbnail_html = f"""
                    <div style="display: flex; flex-direction: column; align-items: center; background-color: #f5e9e3; padding: 10px;">
                        <img src="data:image/png;base64,{encoded_string}" style="width: 150px; height: auto;" /> 
                        <p style="margin-left: 10px;">{thumb_name_with_breaks}</p>
                    </div>
                    """
            
            # Wrap everything in one div
            pie_chart_html = f"""
            <div style="display: flex; flex-direction: column; align-items: start; background-color: #f5e9e3; padding: 10px;"> 
                <div style="display: flex; align-items: center;">  
                    <div style="width: 400px;">{pie_fig.to_html(full_html=False, include_plotlyjs=False)}</div> 
                    {thumbnail_html}
                </div>
                {summary_html}
            </div>
            """

            profile_summary_pie_charts.append(f"""
            <div style="display:inline-block; margin-right: 10px; padding-bottom: 20px;">  
                {pie_chart_html}
            </div>
            """)

    # Arrange pie charts horizontally
    profile_piecharts_html = ''.join(profile_summary_pie_charts)

    profile_summary_html = f'''
    <div>
        {profile_piecharts_html}
    </div>
    '''

    return profile_summary_html

def make_content_summary_html(qctools_content_check_output, sorted_thumbs_dict, paper_bgcolor='#f5e9e3'):
    with open(qctools_content_check_output, 'r') as file:
        lines = file.readlines()

    # Find the line with content filter results
    content_filter_line_index = None
    for i, line in enumerate(lines):
        if line.startswith("Segments found within thresholds of content filter"):
            content_filter_line_index = i
            break

    if content_filter_line_index is None:
        return "Content filter results not found in CSV."

    content_filter_name = lines[content_filter_line_index].split()[-1].strip(':')
    time_ranges = lines[content_filter_line_index + 1:]

    matching_thumbs = [
        (thumb_name, thumb_path)
        for thumb_name, (thumb_path, profile_name, _) in sorted_thumbs_dict.items()
        if content_filter_name in thumb_path  # Simplified matching
    ]


    # Build HTML table
    table_rows = []
    for i, time_range in enumerate(time_ranges):
        thumbnail_html = ""
        if i < len(matching_thumbs):  
            thumb_name, thumb_path = matching_thumbs[i]
            with open(thumb_path, "rb") as image_file:
                encoded_string = b64encode(image_file.read()).decode()
            thumbnail_html = f"""<img src="data:image/png;base64,{encoded_string}" style="width: 150px; height: auto;" />"""

        table_rows.append(f"""
            <tr>
                <td style="text-align: center; padding: 10px;">{thumbnail_html}</td>
                <td style="padding: 10px; white-space: nowrap;">{time_range}</td>  
            </tr>
        """)

    content_summary_html = f"""
    <table style="background-color: {paper_bgcolor}; margin-top: 20px; border-collapse: collapse;"> 
        <tr>
            <th colspan="2" style="padding: 10px;">Segments found within thresholds of content filter {content_filter_name}:</th>
        </tr>
        {''.join(table_rows)}
    </table>
    """

    return content_summary_html

def write_html_report(video_id,report_directory,destination_directory,html_report_path):

    qctools_colorbars_duration_output, qctools_bars_eval_check_output, colorbars_values_output, qctools_content_check_outputs, qctools_profile_check_output, profile_fails_csv, tag_fails_csv, colorbars_eval_fails_csv, difference_csv = find_report_csvs(report_directory)
    
    exiftool_output_path,mediainfo_output_path,ffprobe_output_path,mediaconch_csv = find_qc_metadata(destination_directory)
    
    # Initialize and create html from 
    mc_csv_html, mediaconch_csv_filename = prepare_file_section(mediaconch_csv, lambda path: csv_to_html_table(path, style_mismatched=False, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=True))
    diff_csv_html, difference_csv_filename = prepare_file_section(difference_csv, lambda path: csv_to_html_table(path, style_mismatched=True, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=False))
    exif_file_content, exif_file_filename = prepare_file_section(exiftool_output_path)
    mi_file_content, mi_file_filename = prepare_file_section(mediainfo_output_path)
    ffprobe_file_content, ffprobe_file_filename = prepare_file_section(ffprobe_output_path)

    # Get qct-parse thumbs if they exists
    thumbs_dict = find_qct_thumbs(report_directory)

    if profile_fails_csv:
        profile_fails_csv_path = os.path.join(report_directory, profile_fails_csv)
        failureInfoSummary_profile = summarize_failures(profile_fails_csv_path)

    if tag_fails_csv:
        tag_fails_csv_path = os.path.join(report_directory, tag_fails_csv)
        failureInfoSummary_tags = summarize_failures(tag_fails_csv_path)

    if colorbars_eval_fails_csv:
        colorbars_eval_fails_csv_path =  os.path.join(report_directory, colorbars_eval_fails_csv)
        failureInfoSummary_colorbars = summarize_failures(colorbars_eval_fails_csv_path)
    
    # Create graphs for all existing csv files
    if qctools_bars_eval_check_output:
        colorbars_eval_html = make_profile_piecharts(qctools_bars_eval_check_output,thumbs_dict,failureInfoSummary_colorbars)
    else:
        colorbars_eval_html = None

    if colorbars_values_output:
        colorbars_html = make_color_bars_graphs(video_id,qctools_colorbars_duration_output,colorbars_values_output,thumbs_dict)
    else:
         colorbars_html = None
    
    if qctools_profile_check_output:
        profile_summary_html = make_profile_piecharts(qctools_profile_check_output,thumbs_dict,failureInfoSummary_profile)
    else:
        profile_summary_html = None

    if qctools_content_check_outputs:
        content_summary_html_list = []
        for output_csv in qctools_content_check_outputs:
            content_summary_html = make_content_summary_html(output_csv, thumbs_dict, paper_bgcolor='#f5e9e3')
            content_summary_html_list.append(content_summary_html)
    else:
        content_summary_html_list = None
    
    # Get the absolute path of the script file
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Determine the  path to the image file
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
    logo_image_path = os.path.join(root_dir, 'av_spex_the_logo.png')
    eq_image_path = os.path.join(root_dir, 'germfree_eq.png')

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
    
    if colorbars_html:
        html_template += f"""
        <h3>SMPTE Colorbars vs {video_id} Colorbars</h3>
        {colorbars_html}
        """
    
    if colorbars_eval_html:
        html_template += f"""
        <h3>Values outside of colorbar's thresholds</h3>
        {colorbars_eval_html}
        """

    if profile_summary_html:
        html_template += f"""
        <h3>qct-parse Profile Summary</h3>
        <div style="white-space: nowrap;">
            {profile_summary_html}
        </div>
        """

    if content_summary_html_list:
        for content_summary_html in content_summary_html_list:
            html_template += f"""
            <h3>qct-parse Content Detection</h3>
            <div style="white-space: nowrap;">
                {content_summary_html}
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
