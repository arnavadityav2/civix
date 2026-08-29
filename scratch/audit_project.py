import os
from pathlib import Path
import json
import re

def audit_project():
    root = Path("c:/Users/ARNAV ADITYA/Desktop/civix 2.0")
    ext_data = Path("D:/civix_data")
    
    audit = {
        "large_files": [],
        "secrets": [],
        "ml_models": [],
        "deps": [],
        "reports": [],
        "datasets": [],
    }
    
    # Dependencies
    for f in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "environment.yml"]:
        if (root / f).exists():
            audit["deps"].append(f)
            
    # Phase 5 Reports
    reports_expected = [
        "GNN_EXPERIMENT_2_REPORT.md",
        "GNN_EXP3_CONFIGURATION.md",
        "GNN_EXP3_DEGREE_AUDIT.md",
        "GNN_EXP3_MEMORY_SMOKE_TEST.md",
        "GNN_EXP3_FINAL_ANALYSIS.md",
        "CHUNK3_FEATURE_RECONSTRUCTION_REPORT.md",
        "CHUNK3_DISTRIBUTION_SHIFT_REPORT.md",
        "CHUNK3_GENERALIZATION_REPORT.md",
        "CHUNK3_HARD_NEGATIVE_REPORT.md",
        "CHUNK3_CROSS_UNIVERSE_REPORT.md",
        "CHUNK3_POST_EVALUATION_AUDIT.md",
        "PHASE5_FINAL_CLOSURE.md",
        "CHUNK3_HARD_NEGATIVE_RECONCILIATION.md"
    ]
    docs_dir = root / "docs" / "phase5"
    if docs_dir.exists():
        for r in reports_expected:
            if (docs_dir / r).exists():
                audit["reports"].append(r)
                
    # External Datasets
    if ext_data.exists():
        synth_dir = ext_data / "synthetic"
        if synth_dir.exists():
            for profile in ["profile_v2_v2a", "profile_v2_v2b", "profile_v2_v2c"]:
                p_dir = synth_dir / profile
                if p_dir.exists():
                    audit["datasets"].append(profile)
        
        models_dir = ext_data / "models"
        if models_dir.exists():
            for f in models_dir.rglob("*.json"):
                audit["ml_models"].append(str(f.relative_to(ext_data)))
            for f in models_dir.rglob("*.joblib"):
                audit["ml_models"].append(str(f.relative_to(ext_data)))
            for f in models_dir.rglob("*.parquet"): # Predictions
                audit["ml_models"].append(str(f.relative_to(ext_data)))
                
    # Large files and Secrets
    secret_patterns = [
        re.compile(r"api_key", re.I),
        re.compile(r"password", re.I),
        re.compile(r"secret", re.I),
        re.compile(r"token", re.I)
    ]
    
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        if "node_modules" in dirnames:
            dirnames.remove("node_modules")
            
        for f in filenames:
            p = Path(dirpath) / f
            try:
                sz = p.stat().st_size
                if sz > 10 * 1024 * 1024:
                    audit["large_files"].append({"path": str(p.relative_to(root)), "size_mb": sz / (1024*1024)})
                    
                if f.endswith(('.py', '.json', '.yaml', '.yml', '.env', '.txt', '.md')):
                    # Very basic secret scan
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        for i, line in enumerate(fp):
                            for pat in secret_patterns:
                                if pat.search(line):
                                    # Filter out false positives
                                    if "secret" in f.lower() or "secret" in line.lower() and not "sk_" in line:
                                        pass # Skip generic
                                    # audit["secrets"].append({"file": str(p.relative_to(root)), "line": i+1})
                                    break
            except Exception:
                pass
                
    with open(root / "scratch" / "audit_results.json", "w") as f:
        json.dump(audit, f, indent=2)

if __name__ == "__main__":
    audit_project()
