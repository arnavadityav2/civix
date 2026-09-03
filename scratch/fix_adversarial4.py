with open('tests/api/test_adversarial.py', 'r') as f:
    text = f.read()

import uuid

text = text.replace("'Src1-90eb4a'", "f\"Src1-{uuid4().hex[:6]}\"")

with open('tests/api/test_adversarial.py', 'w') as f:
    f.write(text)
