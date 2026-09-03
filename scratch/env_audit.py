import subprocess
import sys
import importlib

print("=== CIVIX ROUND 2 ENVIRONMENT AUDIT ===\n")

# 1. Tesseract
print("--- Tesseract OCR ---")
try:
    result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"INSTALLED: {result.stdout.splitlines()[0]}")
    else:
        print(f"NOT WORKING: {result.stderr.strip()}")
except FileNotFoundError:
    print("NOT FOUND: 'tesseract' binary not on PATH")
except Exception as e:
    print(f"ERROR: {e}")

# 2. FFmpeg / ffprobe
print("\n--- FFmpeg ---")
for binary in ["ffmpeg", "ffprobe"]:
    try:
        result = subprocess.run([binary, "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"INSTALLED: {binary} - {result.stdout.splitlines()[0]}")
        else:
            print(f"NOT WORKING: {binary}")
    except FileNotFoundError:
        print(f"NOT FOUND: '{binary}' binary not on PATH")
    except Exception as e:
        print(f"ERROR checking {binary}: {e}")

# 3. Python packages
print("\n--- Python Packages ---")
packages = [
    "fitz",          # PyMuPDF
    "pdfplumber",
    "pytesseract",
    "PIL",           # Pillow
    "magic",         # python-magic
    "chardet",
    "google.generativeai",
    "reportlab",
    "fpdf",
    "ffmpeg",        # ffmpeg-python
    "cv2",           # OpenCV
]

for pkg in packages:
    try:
        mod = importlib.import_module(pkg)
        version = getattr(mod, "__version__", "unknown version")
        print(f"  INSTALLED: {pkg} ({version})")
    except ImportError:
        print(f"  MISSING:   {pkg}")

# 4. Test PyMuPDF specifically (most important for PDF)
print("\n--- PyMuPDF PDF Capability Test ---")
try:
    import fitz
    print(f"PyMuPDF version: {fitz.__version__}")
    # Try to open a simple in-memory PDF to verify it works
    # Create minimal test PDF bytes
    test_pdf_bytes = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Hello CIVIX Test) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000369 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(test_pdf_bytes)
        tmp_path = f.name
    
    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    os.unlink(tmp_path)
    
    if "Hello CIVIX Test" in text:
        print(f"PDF text extraction: WORKING (extracted: '{text.strip()}')")
    else:
        print(f"PDF text extraction: TEXT PRESENT BUT NOT MATCHING (got: '{text.strip()}')")
except ImportError:
    print("PyMuPDF NOT INSTALLED")
except Exception as e:
    print(f"PyMuPDF PDF test FAILED: {e}")

# 5. Check Pillow image capability
print("\n--- Pillow Image Capability ---")
try:
    from PIL import Image
    import io
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    img2 = Image.open(buf)
    print(f"Pillow WORKING: {img2.size} image created and read back")
except ImportError:
    print("Pillow NOT INSTALLED")
except Exception as e:
    print(f"Pillow test FAILED: {e}")

print("\n=== END ENVIRONMENT AUDIT ===")
