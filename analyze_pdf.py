import os

def analyze_pdf(filepath):
    print(f"Analyzing {filepath}")
    if not os.path.exists(filepath):
        print("File does not exist.")
        return
    
    stat = os.stat(filepath)
    print(f"Size: {stat.st_size} bytes")
    print(f"Modified: {stat.st_mtime}")
    
    try:
        with open(filepath, 'rb') as f:
            header = f.read(5)
            print(f"Header: {header}")
            if header == b'%PDF-':
                print("Structurally appears to be a PDF (header check).")
            else:
                print("Does NOT appear to be a PDF (header mismatch).")
            
            f.seek(-1024, os.SEEK_END)
            tail = f.read()
            if b'%%EOF' in tail:
                print("EOF marker found (structurally intact).")
            else:
                print("EOF marker NOT found.")
                
        try:
            import pypdf
            reader = pypdf.PdfReader(filepath)
            print(f"Pages: {len(reader.pages)}")
            text = reader.pages[0].extract_text()
            print("Extracted Text Preview:")
            print(text[:200].replace('\n', ' '))
            if "FORENSIC" in text.upper() or "EVIDENCE" in text.upper() or "REPORT" in text.upper():
                print("Semantic content: Contains expected forensic keywords.")
        except Exception as e:
            print(f"PyPDF analysis failed: {e}")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    analyze_pdf(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\civix_golden_evidence\FORENSIC_REPORT_001.pdf")
