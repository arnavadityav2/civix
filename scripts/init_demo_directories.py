import os
from pathlib import Path

evidence_path = Path(r"c:\data\civix_demo\evidence_store")
cctv_path = Path(r"c:\data\civix_demo\cctv_artifacts")

evidence_path.mkdir(parents=True, exist_ok=True)
cctv_path.mkdir(parents=True, exist_ok=True)

print(f"[PASS] Demo Evidence Root Created: {evidence_path.exists()} ({evidence_path})")
print(f"[PASS] Demo CCTV Root Created: {cctv_path.exists()} ({cctv_path})")
