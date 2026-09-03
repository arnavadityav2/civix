import os
import sys

# Add civix 2.0 to path
sys.path.insert(0, os.path.abspath('.'))

from civix_api.services.processors.resolver import ProcessorResolver

DOCS_DIR = "scratch/test_docs_upgraded"

all_good = True
for filename in os.listdir(DOCS_DIR):
    path = os.path.join(DOCS_DIR, filename)
    with open(path, "rb") as f:
        file_bytes = f.read()
    
    try:
        mime, result = ProcessorResolver.resolve(file_bytes, filename)
        if result.success:
            print(f"[OK] {filename} -> MIME: {mime}")
        else:
            print(f"[FAIL] {filename} -> MIME: {mime}, Error: {result.error}")
            all_good = False
    except Exception as e:
        print(f"[ERROR] {filename} -> {e}")
        all_good = False

if all_good:
    print("\nSTATIC VALIDATION PASSED. All files are readable by processors.")
else:
    print("\nSTATIC VALIDATION FAILED.")
    sys.exit(1)
