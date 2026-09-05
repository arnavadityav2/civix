import os
import re
import glob

folder = r"C:\Users\ARNAV ADITYA\Desktop\case files md"

def load_file(name):
    path = os.path.join(folder, name)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

part1 = load_file("01_Universe_Bible_Part1.md")
part2 = load_file("02_Universe_Bible_Part2_CaseMatrix.md")
part3 = load_file("CIVIX_2.0_UNIVERSE_BIBLE_PART_3.md")
evd_manifest = load_file("CIVIX_2.0_CASES_EVIDENCE_MANIFEST.md")
photo_manifest = load_file("CIVIX_2.0_PERSONS_PHOTO_MANIFEST.md")
exec_guide = load_file("ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md")

print("=== DEEP DRIFT & CONNECTIVITY AUDIT ===\n")

# 1. Check Person ID consistency between Part 2, Part 3, and Photo Manifest
p_part2 = set(re.findall(r"P\d{4}", part2))
p_part3 = set(re.findall(r"P\d{4}", part3))
p_photo = set(re.findall(r"P\d{4}", photo_manifest))

print(f"Persons in Part 2 Case Matrix: {len(p_part2)}")
print(f"Persons in Part 3 Ground Truth: {len(p_part3)}")
print(f"Persons in Photo Manifest: {len(p_photo)}")

photo_not_in_part2 = p_photo - p_part2
if photo_not_in_part2:
    print(f"WARN: Person IDs in Photo Manifest but missing from Part 2: {sorted(list(photo_not_in_part2))}")
else:
    print("SUCCESS: 100% of Person IDs in Photo Manifest exist in Part 2 Case Matrix!")

part2_not_in_photo = p_part2 - p_photo
if part2_not_in_photo:
    print(f"INFO: Person IDs in Part 2 not explicitly in Photo Manifest (Background/Unlisted): {sorted(list(part2_not_in_photo))}")

# 2. Check Hero Cases Alignment
hero_matrix = {
    "HERO-01": ["CIVIX-001", "CIVIX-027", "P0075", "T0011"],
    "HERO-02": ["CIVIX-036", "CIVIX-010", "P0095", "07AARCA1234J1Z1"],
    "HERO-03": ["CIVIX-019", "DL-8C-AB-1234", "P0045", "P0050"],
    "HERO-04": ["CIVIX-009", "CIVIX-003", "CIVIX-044", "P0001", "P0120"],
    "HERO-05": ["CIVIX-027", "CIVIX-019", "357891049234561"],
    "HERO-06": ["CIVIX-044", "CIVIX-047", "CIVIX-050", "P0200"],
    "HERO-07": ["CIVIX-051", "P0156", "ORG-031"],
    "HERO-08": ["CIVIX-032", "CIVIX-014", "P0073"],
    "HERO-09": ["CIVIX-044", "CIVIX-046", "P0130"],
    "HERO-10": ["CIVIX-038", "P0100"],
    "HERO-11": ["CIVIX-003", "CIVIX-022", "HR-06UH-3818"],
    "HERO-12": ["P0003", "P0133"]
}

print("\n--- HERO CASE CONNECTIVITY CHECK ---")
all_docs_text = part1 + "\n" + part2 + "\n" + part3 + "\n" + evd_manifest + "\n" + photo_manifest

for hero, anchors in hero_matrix.items():
    missing_anchors = [a for a in anchors if a not in all_docs_text]
    if missing_anchors:
        print(f"FAIL: {hero} missing anchors in universe text: {missing_anchors}")
    else:
        print(f"PASS: {hero} anchors 100% verified ({', '.join(anchors)})")

# 3. Check Evidence ID alignment between Part 2 and Evidence Manifest
evd_part2 = set(re.findall(r"EVD-\d{3}-\d{3}", part2))
evd_manifest_ids = set(re.findall(r"EVD-\d{3}-\d{3}", evd_manifest))

print(f"\nDistinct Evidence IDs in Part 2: {len(evd_part2)}")
print(f"Distinct Evidence IDs in Evidence Manifest: {len(evd_manifest_ids)}")

evd_diff = evd_part2 - evd_manifest_ids
print(f"Evidence IDs in Part 2 covered in Evidence Manifest: {len(evd_part2 & evd_manifest_ids)} / {len(evd_part2)}")

# 4. Check Network Interlocks
networks = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
print("\n--- NETWORK INTERLOCKS CHECK ---")
for n in networks:
    count_part1 = len(re.findall(n, part1))
    count_part2 = len(re.findall(n, part2))
    count_part3 = len(re.findall(n, part3))
    print(f"Network {n}: Mentioned {count_part1}x in Part 1, {count_part2}x in Part 2, {count_part3}x in Part 3")

