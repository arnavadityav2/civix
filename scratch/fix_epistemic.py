import os

for path in ['tests/api/test_investigator_assertions.py', 'tests/api/test_graph_acl.py']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("'VERIFIED'", "'CONFIRMED'")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
