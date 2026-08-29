"""Train all 4 baseline models in sequence, then evaluate + adversarial."""
import subprocess
import sys

PYTHON = sys.executable
CWD = r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0"

def run(cmd):
    print(f"\n{'='*60}\nRUNNING: {' '.join(cmd)}\n{'='*60}")
    result = subprocess.run(cmd, cwd=CWD, capture_output=False)
    if result.returncode != 0:
        print(f"FAILED with code {result.returncode}")
        sys.exit(result.returncode)
    print("OK")

run([PYTHON, "-m", "civix_ml", "train", "--model", "logistic"])
run([PYTHON, "-m", "civix_ml", "train", "--model", "random_forest"])
run([PYTHON, "-m", "civix_ml", "train", "--model", "xgboost"])
run([PYTHON, "-m", "civix_ml", "train", "--model", "isolation_forest"])
run([PYTHON, "-m", "civix_ml", "evaluate"])
run([PYTHON, "-m", "civix_ml", "adversarial"])
run([PYTHON, "civix_ml/evaluation/synthetic_gap.py"])

print("\n\nALL STEPS COMPLETE")
