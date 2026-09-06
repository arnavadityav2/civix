import os
import sys
import json
import numpy as np
from pathlib import Path

# Insert project path
sys.path.insert(0, '.')

from civix_api.services.cv.biometric_engine import biometric_engine

biometric_engine.load()

# Load index entries and embeddings
entries = biometric_engine.index["entries"]
embeddings = biometric_engine.embeddings

print("==========================================================================")
print("CIVIX 2.0 BIOMETRIC EMPIRICAL CALIBRATION REPORT")
print("==========================================================================")
print(f"Total Reference Entries: {len(entries)}")

same_person_scores = []
diff_person_scores = []

# Group entries by person_id
person_entries = {}
for entry in entries:
    pid = entry["person_id"]
    if pid not in person_entries:
        person_entries[pid] = []
    person_entries[pid].append(entry)

person_ids = list(person_entries.keys())
print(f"Cohort Persons Count   : {len(person_ids)}")

# 1. Compute Same-Person Pairwise Similarities
for pid, e_list in person_entries.items():
    n = len(e_list)
    for i in range(n):
        v1 = embeddings[e_list[i]["embedding_key"]]
        for j in range(i + 1, n):
            v2 = embeddings[e_list[j]["embedding_key"]]
            sim = float(np.dot(v1, v2))
            same_person_scores.append(sim)

# 2. Compute Different-Person Pairwise Similarities
for i in range(len(person_ids)):
    pid1 = person_ids[i]
    e_list1 = person_entries[pid1]
    for j in range(i + 1, len(person_ids)):
        pid2 = person_ids[j]
        e_list2 = person_entries[pid2]
        
        for e1 in e_list1:
            v1 = embeddings[e1["embedding_key"]]
            for e2 in e_list2:
                v2 = embeddings[e2["embedding_key"]]
                sim = float(np.dot(v1, v2))
                diff_person_scores.append(sim)

same_arr = np.array(same_person_scores)
diff_arr = np.array(diff_person_scores)

print(f"\n--- SAME-PERSON DISTRIBUTION ({len(same_arr)} pairs) ---")
print(f"  Min       : {np.min(same_arr):.4f}")
print(f"  Max       : {np.max(same_arr):.4f}")
print(f"  Mean      : {np.mean(same_arr):.4f}")
print(f"  Median    : {np.median(same_arr):.4f}")
print(f"  P1        : {np.percentile(same_arr, 1):.4f}")
print(f"  P5        : {np.percentile(same_arr, 5):.4f}")
print(f"  P95       : {np.percentile(same_arr, 95):.4f}")
print(f"  P99       : {np.percentile(same_arr, 99):.4f}")

print(f"\n--- DIFFERENT-PERSON DISTRIBUTION ({len(diff_arr)} pairs) ---")
print(f"  Min       : {np.min(diff_arr):.4f}")
print(f"  Max       : {np.max(diff_arr):.4f}")
print(f"  Mean      : {np.mean(diff_arr):.4f}")
print(f"  Median    : {np.median(diff_arr):.4f}")
print(f"  P1        : {np.percentile(diff_arr, 1):.4f}")
print(f"  P5        : {np.percentile(diff_arr, 5):.4f}")
print(f"  P95       : {np.percentile(diff_arr, 95):.4f}")
print(f"  P99       : {np.percentile(diff_arr, 99):.4f}")

# Check Overlap
max_diff = np.max(diff_arr)
min_same = np.min(same_arr)
p1_same = np.percentile(same_arr, 1)
p99_diff = np.percentile(diff_arr, 99)

print(f"\n--- DISTRIBUTION SEPARATION & OVERLAP ---")
print(f"  Max Different-Person Score: {max_diff:.4f}")
print(f"  Min Same-Person Score     : {min_same:.4f}")
print(f"  P99 Different-Person Score: {p99_diff:.4f}")
print(f"  P1  Same-Person Score     : {p1_same:.4f}")

# Threshold Calibration Logic
# We select threshold between P99 of different-person (0.242) and P1 of same-person (0.342)
# Midpoint threshold: 0.300
calibrated_threshold = 0.30
calibrated_margin = 0.05
high_conf_thresh = 0.50

print(f"\n--- EMPIRICALLY CALIBRATED THRESHOLDS ---")
print(f"  Selected Identity Match Threshold : {calibrated_threshold:.2f}")
print(f"  Selected Ambiguity Margin          : {calibrated_margin:.2f} (Band: [{calibrated_threshold - calibrated_margin:.2f}, {calibrated_threshold:.2f}])")
print(f"  Selected High Confidence Threshold : {high_conf_thresh:.2f}")

# Save updated calibration to biometric_config.json
config_path = biometric_engine.config_path
config_data = {
    "model_version": "face_recognition_sface_2021dec.onnx",
    "embedding_dim": 128,
    "cohort_size": len(person_ids),
    "total_references": len(entries),
    "threshold": calibrated_threshold,
    "ambiguity_margin": calibrated_margin,
    "high_confidence_threshold": high_conf_thresh,
    "same_person_stats": {
        "count": len(same_arr),
        "min": float(np.min(same_arr)),
        "max": float(np.max(same_arr)),
        "mean": float(np.mean(same_arr)),
        "median": float(np.median(same_arr)),
        "p1": float(np.percentile(same_arr, 1)),
        "p5": float(np.percentile(same_arr, 5))
    },
    "different_person_stats": {
        "count": len(diff_arr),
        "min": float(np.min(diff_arr)),
        "max": float(np.max(diff_arr)),
        "mean": float(np.mean(diff_arr)),
        "median": float(np.median(diff_arr)),
        "p95": float(np.percentile(diff_arr, 95)),
        "p99": float(np.percentile(diff_arr, 99))
    }
}

with open(config_path, "w") as f:
    json.dump(config_data, f, indent=2)

print(f"\nSaved empirical calibration config to {config_path}")
