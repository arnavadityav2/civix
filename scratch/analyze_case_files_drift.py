import os
import re
import glob

folder = r"C:\Users\ARNAV ADITYA\Desktop\case files md"
files = glob.glob(os.path.join(folder, "*.md"))

print(f"Found {len(files)} files to analyze:")
for f in files:
    size = os.path.getsize(f)
    print(f" - {os.path.basename(f)} ({size} bytes)")

all_text = {}
for f in files:
    with open(f, "r", encoding="utf-8", errors="ignore") as file:
        all_text[os.path.basename(f)] = file.read()

# Extract all CIVIX Case IDs
cases_in_part2 = set(re.findall(r"CIVIX-\d{3}", all_text.get("02_Universe_Bible_Part2_CaseMatrix.md", "")))
print(f"\nTotal Cases in Part 2 Case Matrix: {len(cases_in_part2)}")

# Extract all Person IDs (P0001 to P0320)
persons = set(re.findall(r"P\d{4}", "\n".join(all_text.values())))
print(f"Total Person IDs referenced across all files: {len(persons)}")

# Extract Hero Cases referenced
hero_cases = set(re.findall(r"HERO-\d{2}", "\n".join(all_text.values())))
print(f"Hero Cases referenced: {sorted(list(hero_cases))}")

# Check cross-case references in Part 2
cross_cases = set(re.findall(r"CIVIX-\d{3}", "\n".join(all_text.values())))
print(f"Total distinct CIVIX case IDs across all documents: {len(cross_cases)}")
missing_cases = [f"CIVIX-{i:03d}" for i in range(1, 56) if f"CIVIX-{i:03d}" not in cross_cases]
print(f"Missing Case IDs in 1..55 range: {missing_cases}")

# Detailed file breakdown
for fname, content in all_text.items():
    case_refs = len(set(re.findall(r"CIVIX-\d{3}", content)))
    person_refs = len(set(re.findall(r"P\d{4}", content)))
    evd_refs = len(set(re.findall(r"EVD-[\w-]+", content)))
    print(f"\n[{fname}]")
    print(f"  - Case IDs: {case_refs}")
    print(f"  - Person IDs: {person_refs}")
    print(f"  - Evidence IDs: {evd_refs}")
