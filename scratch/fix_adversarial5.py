with open('tests/api/test_adversarial.py', 'r') as f:
    text = f.read()

import re

# Fix the syntax error by using standard string for python then string formatting, or just use sql gen_random_uuid
text = re.sub(r'f"Src1-\{uuid4\(\)\.hex\[:6\]\}"', "'Src1-' || substr(cast(gen_random_uuid() as text), 1, 6)", text)

with open('tests/api/test_adversarial.py', 'w') as f:
    f.write(text)
