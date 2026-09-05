from pathlib import Path

store = Path(r"c:\data\civix_demo\evidence_store")
if store.exists():
    files = list(store.glob("**/*"))
    print(f"Total files in store: {len(files)}")
    for f in files[:20]:
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size} bytes)")
