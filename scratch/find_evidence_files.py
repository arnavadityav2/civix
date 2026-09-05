import os
from pathlib import Path

target_file = "f3e86726c4af5b94c30b11edb9a81ff969090b3ea5f6f70e24415600b04b04cd.pdf"

search_roots = [
    Path(r"c:\data\civix_demo"),
    Path(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0"),
    Path(r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\9326d50b-d2ec-4488-9f30-53ba4f90f5b1")
]

for root in search_roots:
    print(f"Searching in {root}...")
    if not root.exists():
        continue
    for p in root.glob(f"**/{target_file}"):
        print("FOUND:", p)

# Also check all files in c:\data\civix_demo\evidence_store or related
demo_dir = Path(r"c:\data\civix_demo")
if demo_dir.exists():
    print("\nListing c:\\data\\civix_demo subdirectories:")
    for child in demo_dir.iterdir():
        print(f"  {child}")
