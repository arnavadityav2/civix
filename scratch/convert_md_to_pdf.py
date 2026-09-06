import os
import subprocess
import markdown

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

MD_FILES = [
    r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\CIVIX_2.0_PROJECT_MASTER_REFERENCE.md",
    r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\CIVIX_2.0_TECHNICAL_ARCHITECTURE_AND_SCALABILITY.md",
    r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\CIVIX_2.0_REAL_WORLD_IMPLEMENTATION_ROADMAP.md",
    r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\CIVIX_2.0_PRESENTATION_AND_DEMO_PLAYBOOK.md",
    r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\CIVIX_2.0_ENGINEERING_KNOWLEDGE_BASE.md",
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-right {{
            content: counter(page);
        }}
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        background-color: #ffffff;
        line-height: 1.6;
        font-size: 13px;
        padding: 0;
        margin: 0;
    }}
    h1 {{
        font-size: 24px;
        color: #0f172a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 8px;
        margin-top: 0;
        margin-bottom: 16px;
    }}
    h2 {{
        font-size: 18px;
        color: #1e3a8a;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 4px;
        margin-top: 24px;
        margin-bottom: 12px;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 14px;
        color: #2563eb;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}
    p, li {{
        font-size: 12px;
        color: #334155;
    }}
    code {{
        font-family: "Cascadia Code", Consolas, Monaco, "Courier New", monospace;
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 11px;
    }}
    pre {{
        background-color: #0f172a;
        color: #f8fafc;
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        font-size: 11px;
        line-height: 1.4;
        page-break-inside: avoid;
    }}
    pre code {{
        background-color: transparent;
        color: inherit;
        padding: 0;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
        margin-bottom: 16px;
        font-size: 11px;
        page-break-inside: avoid;
    }}
    th {{
        background-color: #1e293b;
        color: #ffffff;
        text-align: left;
        padding: 8px 10px;
        font-weight: 600;
    }}
    td {{
        border: 1px solid #cbd5e1;
        padding: 6px 10px;
        color: #334155;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    blockquote {{
        border-left: 4px solid #3b82f6;
        background-color: #eff6ff;
        margin: 12px 0;
        padding: 8px 16px;
        color: #1e40af;
        border-radius: 0 4px 4px 0;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 20px 0;
    }}
</style>
</head>
<body>
{content}
</body>
</html>
"""

def convert_md_to_pdf(md_path):
    pdf_path = md_path.replace(".md", ".pdf")
    html_path = md_path.replace(".md", ".temp.html")
    
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'codehilite'])
    full_html = HTML_TEMPLATE.format(content=html_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    
    print(f"Converting {os.path.basename(md_path)} -> {os.path.basename(pdf_path)}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(html_path):
        os.remove(html_path)
        
    if os.path.exists(pdf_path):
        print(f"SUCCESS: Created {pdf_path}")
    else:
        print(f"ERROR: Failed to create {pdf_path}. Stdout: {result.stdout}, Stderr: {result.stderr}")

def main():
    for md_file in MD_FILES:
        convert_md_to_pdf(md_file)

if __name__ == "__main__":
    main()
