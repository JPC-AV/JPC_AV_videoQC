#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
from ..utils.log_setup import logger
from ..utils.find_config import config_path

def exiftool_to_csv(exiftool_output_path,exiftool_csv_path):
    # creates a dictionary of expected keys and values
    expected_exif_values = config_path.config_dict['exiftool_values']
    
    with open(exiftool_output_path, 'r') as file:
    # open exiftool text file as variable "file"
        lines = file.readlines()
        # define variable 'lines' as all individual lines in file (to be parsed in next "for loop")
    
    exif_data = {}
    
    for line in lines:
    # for each line in exiftool text file
        line = line.strip()
        # strips line of blank space with python function strip()
        key, value = [x.strip() for x in line.split(":", 1)]
        #assign variable "key" to string before ":" and variable "value" to string after ":"
        exif_data[key] = value
        # value is matched to the key, in a key:value pair

    # Writing to a CSV file
    with open(exiftool_csv_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Exif Field', 'Actual Exif Data Value', 'Expected Value'])
        
        for key in exif_data:
            exif_value = exif_data[key]
            expected_value = expected_exif_values.get(key, 'N/A')
            csv_writer.writerow([key, exif_value, expected_value])

    

# Read CSV files and convert them to HTML tables
def csv_to_html_table(csv_file, style_mismatched=False, mismatch_color="#ff9999", check_fail=False):
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
            elif style_mismatched and i == 1 and row[2] != 'N/A' and row[1] != row[2]:
                table_html += f'    <td style="background-color: {mismatch_color};">{cell}</td>\n'
            elif style_mismatched and i == 2 and row[2] != 'N/A' and row[1] != row[2]:
                table_html += f'    <td style="background-color: {mismatch_color};">{cell}</td>\n'
            else:
                table_html += f'    <td>{cell}</td>\n'
        table_html += '  </tr>\n'
    table_html += '</table>\n'
    return table_html

def write_html_report(video_id,mediaconch_csv,difference_csv,exiftool_csv_path,html_report_path):
    # Initialize the HTML sections for the CSV tables
    mc_csv_html = ''
    diff_csv_html = ''
    exif_html = ''
    mediaconch_csv_filename = ''
    difference_csv_filename = ''
    exiftool_csv_filename = ''

    # Read and convert mediaconch_csv if it exists
    if mediaconch_csv:
        mc_csv_html = csv_to_html_table(mediaconch_csv, style_mismatched=False, mismatch_color="#ffbaba", check_fail=True) 
        mediaconch_csv_filename = os.path.basename(mediaconch_csv)

    # Read and convert difference_csv if it exists
    if difference_csv:
        diff_csv_html = csv_to_html_table(difference_csv)
        difference_csv_filename = os.path.basename(difference_csv)

     # Read and convert exiftool_csv if it exists
    if exiftool_csv_path:
        exif_html = csv_to_html_table(exiftool_csv_path, style_mismatched=True, mismatch_color="#ffbaba")
        exiftool_csv_filename = os.path.basename(exiftool_csv_path)
    
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
                background-color: #fff3ee;
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
        </style>
    </head>
    <body>
        <h1>AV Spex Report</h1>
        <h2>{video_id}</h2>
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

    if exif_html:
        html_template += f"""
        <h3>{exiftool_csv_filename}</h3>
        {exif_html}
        """

    html_template += """
    </body>
    </html>
    """

    # Write the HTML file
    with open(html_report_path, 'w') as f:
        f.write(html_template)

    logger.info("\nHTML report generated successfully!")
