#!/usr/bin/env python3

import csv
import os
import json
from datetime import datetime

def csv_to_html_log_viewer(csv_file_path: str, output_html_path: str = None):
    if not output_html_path:
        output_html_path = csv_file_path.replace('.csv', '.html')
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Log Viewer</title>
        <style>
            body {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                background-color: #1e1e1e;
                color: #d4d4d4;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .action-record {
                background-color: #2d2d30;
                border: 2px solid #007acc;
                border-radius: 8px;
                margin: 20px 0;
                padding: 15px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            
            .action-header {
                background-color: #007acc;
                color: white;
                padding: 10px;
                margin: -15px -15px 15px -15px;
                border-radius: 6px 6px 0 0;
                font-weight: bold;
                text-align: center;
            }
            
            .round-separator {
                background-color: #4a4a4a;
                color: #ffd700;
                padding: 15px;
                margin: 30px 0;
                border-radius: 8px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #ffd700;
            }
            
            .prompt-marker {
                background-color: #1a472a;
                color: #4ec9b0;
                padding: 8px;
                margin: 10px 0;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
                border-left: 4px solid #4ec9b0;
            }
            
            .prompt-content {
                background-color: #0d1117;
                color: #58a6ff;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border: 1px solid #30363d;
                white-space: pre-wrap;
                font-size: 14px;
                line-height: 1.4;
                overflow-x: auto;
            }
            
            .data-row {
                background-color: #161b22;
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
                border-left: 3px solid #58a6ff;
            }
            
            .field-label {
                color: #f85149;
                font-weight: bold;
            }
            
            .field-value {
                color: #d4d4d4;
                margin-left: 10px;
            }
            
            .timestamp {
                color: #7c3aed;
                font-weight: bold;
            }
            
            .user {
                color: #10b981;
                font-weight: bold;
            }
            
            .action {
                color: #f59e0b;
                font-weight: bold;
            }
            
            .content {
                color: #e5e7eb;
                background-color: #374151;
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center; color: #58a6ff;">🤖 Social Network Simulation Log Viewer</h1>
    """
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            
            if not rows:
                html_content += "<p>Log file is empty</p>"
                return
                
            headers = rows[0] if rows else []
            
            for i, row in enumerate(rows[1:], 1):
                if row and row[0].startswith("=========="):
                    html_content += f'<div class="round-separator">{row[0]}</div>'
                    continue
                    
                if row and row[0].startswith("--------------ACTION RECORD"):
                    html_content += f'<div class="action-record"><div class="action-header">{row[0]}</div>'
                    continue
                    
                if row and row[0].startswith(">>> PROMPT START <<<"):
                    html_content += f'<div class="prompt-marker">{row[0]}</div>'
                    continue
                    
                if row and row[0].startswith("🔵 [BLUE PROMPT START] 🔵"):
                    prompt_content = row[0].replace("🔵 [BLUE PROMPT START] 🔵\n", "").replace("\n🔵 [BLUE PROMPT END] 🔵", "")
                    html_content += f'<div class="prompt-content">{prompt_content}</div>'
                    continue
                    
                if row and row[0].startswith("🔵 [BLUE PROMPT END] 🔵"):
                    html_content += '</div>'
                    continue
                
                if row and any(cell.strip() for cell in row):
                    html_content += '<div class="data-row">'
                    for j, (header, value) in enumerate(zip(headers, row)):
                        if value.strip():
                            if header == "timestamp":
                                html_content += f'<span class="field-label">{header}:</span><span class="timestamp field-value">{value}</span><br>'
                            elif header == "user":
                                html_content += f'<span class="field-label">{header}:</span><span class="user field-value">{value}</span><br>'
                            elif header == "action":
                                html_content += f'<span class="field-label">{header}:</span><span class="action field-value">{value}</span><br>'
                            elif header == "content":
                                html_content += f'<span class="field-label">{header}:</span><div class="content">{value}</div>'
                            else:
                                html_content += f'<span class="field-label">{header}:</span><span class="field-value">{value}</span><br>'
                    html_content += '</div>'
    
    except FileNotFoundError:
        html_content += f"<p style='color: #f85149;'>Error: File not found: {csv_file_path}</p>"
    except Exception as e:
        html_content += f"<p style='color: #f85149;'>Error: {str(e)}</p>"
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML log viewer generated: {output_html_path}")
    return output_html_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        html_file = sys.argv[2] if len(sys.argv) > 2 else None
        csv_to_html_log_viewer(csv_file, html_file)
    else:
        print("Usage: python log_viewer.py <csv_file> [html_output_file]")
