#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
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

def find_qct_thumbs(destination_directory):
    thumbs_dict = {}
    color_bars_entry = None
    thumb_exports_dir = os.path.join(destination_directory, 'ThumbExports')
    
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


def write_html_report(video_id,destination_directory,mediaconch_csv,difference_csv,qctools_check_output,exiftool_output_path,mediainfo_output_path,ffprobe_output_path,html_report_path):
    
    # Initialize and create html from 
    mc_csv_html, mediaconch_csv_filename = prepare_file_section(mediaconch_csv, lambda path: csv_to_html_table(path, style_mismatched=False, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=True))
    diff_csv_html, difference_csv_filename = prepare_file_section(difference_csv, lambda path: csv_to_html_table(path, style_mismatched=True, mismatch_color="#ffbaba", match_color="#d2ffed", check_fail=False))
    qct_summary_content, qct_summary_filename = prepare_file_section(qctools_check_output)
    exif_file_content, exif_file_filename = prepare_file_section(exiftool_output_path)
    mi_file_content, mi_file_filename = prepare_file_section(mediainfo_output_path)
    ffprobe_file_content, ffprobe_file_filename = prepare_file_section(ffprobe_output_path)
    
    # Get the absolute path of the script file
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Determine the  path to the image file
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
    logo_image_path = os.path.join(root_dir, 'av_spex_the_logo.png')
    eq_image_path = os.path.join(root_dir, 'germfree_eq.png')

    # Get qct-parse thumbs if they exists
    thumbs_dict = find_qct_thumbs(destination_directory)

    #print(f"!!!!! debugging message!!!!! \n\n {thumbs_dict}")

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
    
    if qctools_check_output:
        html_template += f"""
        <h3>{qct_summary_filename}</h3>
        <pre>{qct_summary_content}</pre>
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
