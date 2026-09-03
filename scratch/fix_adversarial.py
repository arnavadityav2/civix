import re

with open('tests/api/test_adversarial.py', 'r') as f:
    text = f.read()

text = text.replace("'jurisdiction': 'A'}", "'jurisdiction': 'A', 'created_by': str(user_a)}")
text = text.replace("'jurisdiction': 'B'}", "'jurisdiction': 'B', 'created_by': str(user_b)}")
text = text.replace("'jurisdiction': 'D'}", "'jurisdiction': 'D', 'created_by': str(user_a)}")

with open('tests/api/test_adversarial.py', 'w') as f:
    f.write(text)
