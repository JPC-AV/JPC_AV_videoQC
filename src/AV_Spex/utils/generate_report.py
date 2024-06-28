#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
from ..utils.log_setup import logger

# Read CSV files and convert them to HTML tables
def csv_to_html_table(csv_file):
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
        for cell in row:
            table_html += f'    <td>{cell}</td>\n'
        table_html += '  </tr>\n'
    table_html += '</table>\n'
    return table_html

def write_html_report(video_id,mediaconch_csv,difference_csv,html_report_path):
    # Read CSV files
    mc_csv_html = csv_to_html_table(mediaconch_csv)
    diff_csv2_html = csv_to_html_table(difference_csv)
    mediaconch_csv_filename = os.path.basename(mediaconch_csv)
    difference_csv_filename = os.path.basename(difference_csv)
    
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
                background-color: #f5e9e3;
                color: #011054;
            }}
            h1 {{
                font-size: 24px;
                text-align: center;
                margin-top: 20px;
                color: #378d6a;
            }}
            h2 {{
                font-size: 20px;
                margin-top: 30px;
                color: #d79eaf;
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
                border: 1px solid #4d2b12;
            }}
            th, td {{
                border: 1px solid #4d2b12;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #eee2dc;
                font-weight: bold;
                color: #4d2b12;
            }}
        </style>
    </head>
    <body>
        <h1>AV Spex Report</h1>
        <h2>{video_id}</h2>

        <h3>{mediaconch_csv_filename}</h3>
        {mc_csv_html}

        <h3>{difference_csv_filename}</h3>
        {diff_csv2_html}
    </body>
    </html>
    """

    # Write the HTML file
    with open(html_report_path, 'w') as f:
        f.write(html_template)

    logger.info("\nHTML report generated successfully!")
