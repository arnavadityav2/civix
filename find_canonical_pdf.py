import os
import hashlib

def find_canonical_pdf(expected_hash):
    print(f"Searching for PDF with hash: {expected_hash}")
    search_dirs = [
        "civix_evidence_store",
        "tests",
        "database",
        "docs",
        "scratch",
        ".",
    ]
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            # Exclude some large irrelevant dirs
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if ".git" in dirs:
                dirs.remove(".git")
                
            for file in files:
                if file.lower().endswith(".pdf"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "rb") as f:
                            h = hashlib.sha256(f.read()).hexdigest().upper()
                            if h == expected_hash:
                                print(f"FOUND MATCH: {path}")
                                return path
                    except Exception as e:
                        pass
    print("No match found.")
    return None

if __name__ == "__main__":
    find_canonical_pdf("09C1D456335A2519F961417072343E5DF959F3C2CE5D34D805C883F43D918BDC")
