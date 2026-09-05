import os

SPATIAL_DIR = os.path.abspath("frontend/src/components/spatial")

for root, dirs, files in os.walk(SPATIAL_DIR):
    for f in files:
        if f.endswith(".tsx"):
            path = os.path.join(root, f)
            print(f"=== File: {f} ===")
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
                if "animation" in content.lower() or "scrub" in content.lower() or "play" in content.lower():
                    print(f"  Found playback/scrubber references in {f}")
