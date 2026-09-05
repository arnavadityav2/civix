import json

with open("scratch/db_schema_audit.json") as f:
    data = json.load(f)

print("TABLE NAME | ROW COUNT | COLUMN COUNT")
print("-" * 50)
for t, info in data.items():
    print(f"{t:<35} | {info['count']:<8} | {len(info['columns'])}")
