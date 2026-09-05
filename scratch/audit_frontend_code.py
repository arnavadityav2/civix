import os
import re

FRONTEND_DIR = os.path.abspath("frontend/src")

suspicious_patterns = [
    (re.compile(r'mock[A-Z]\w+'), "Mock variable name"),
    (re.compile(r'hardcoded', re.IGNORECASE), "Hardcoded comment/ref"),
    (re.compile(r'dummy[A-Z]\w+'), "Dummy variable name"),
    (re.compile(r'placeholder', re.IGNORECASE), "Placeholder ref"),
    (re.compile(r'\[\s*\{\s*id:\s*["\']'), "Inline mock object array")
]

findings = []

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith((".ts", ".tsx")):
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, os.path.abspath("."))
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
                for idx, line in enumerate(lines, 1):
                    for pat, label in suspicious_patterns:
                        if pat.search(line) and not "node_modules" in rel_path and not "test" in rel_path.lower():
                            # Filter out harmless UI defaults
                            if "className" in line or "import" in line or "interface" in line or "type " in line:
                                continue
                            findings.append({
                                "file": rel_path,
                                "line": idx,
                                "label": label,
                                "code": line.strip()
                            })

print(f"Total suspicious findings: {len(findings)}")
for find in findings[:25]:
    print(f"[{find['file']}:{find['line']}] ({find['label']}) -> {find['code']}")
