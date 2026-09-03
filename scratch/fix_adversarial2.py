with open('tests/api/test_adversarial.py', 'r') as f:
    text = f.read()

text = text.replace("'TELCO', 'RELIABLE')", "'TELECOM', 0.9)")
text = text.replace("source_type, reliability", "agency_type, reliability_score")

with open('tests/api/test_adversarial.py', 'w') as f:
    f.write(text)
