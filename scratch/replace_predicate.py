import os
path = r'tests/api/test_investigator_assertions.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('"ASSOCIATED_WITH"', '"KNOWN_ASSOCIATE_OF"')
content = content.replace("'ASSOCIATED_WITH'", "'KNOWN_ASSOCIATE_OF'")
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
