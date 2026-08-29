import re

path = r'C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\4d2a421e-8d1d-4a48-8703-7eae27170647\synthetic_world.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. canonical device/IMEI correction (Fix DEV-06/DEV-07 conflict)
content = content.replace('| DEV-06 | Handset | IMEI-8866 | Bhupendra | 9777888999 (Constant) |', '| DEV-06 | Handset | IMEI-8866 | Bhupendra | 9777888999 (Constant) |')
content = content.replace('| DEV-07 | Handset | IMEI-8866 | Bhupendra | **9555666777 (Jun 15-28)** -> Shared Ravi\'s SIM |', '')
content = content.replace('9777888999 (Constant)', '9777888999 (Constant), **9555666777 (Jun 15-28)** (Ravi\'s SIM temporarily hosted)')

# 2. canonical property IDs (Align Khasra 45/47 to properties)
content = content.replace('Khasra 47', 'Khasra 45') # Ensure consistent referencing for Babita

# 3. canonical Dinesh financial numbers (Standardize ₹1.5L vs ₹3.25L vs ₹6.2L)
content = content.replace('₹1.5L deposit', '₹3.25L deposit')
content = content.replace('₹6,20,000 deposits', '₹3,25,000 deposits')

# 4. canonical Babita case/property relationship
content = re.sub(r'\"cases\": \[\"FIR-2026-0198\"\]', '\"cases\": [\"FIR-2026-0198\", \"FIR-2026-0182\"]', content)

# 5. corrected periodicity definition
content = content.replace('Exact 30 days', 'Approx. Monthly')

# 6. deterministic RNG specification
rng_spec = '''
## 15a. Deterministic Generator Settings

To ensure the world is completely reproducible for validation, the generator must use these exact settings:
```yaml
generator:
  world_version: 2.1
  world_seed: 20260828
  rng_algorithm: PCG64
  timezone: Asia/Kolkata
  date_range:
    start: 2026-06-01
    end: 2026-08-31
```
*(Every file generation module must instantiate an independent RNG stream using this seed)*
'''
content = content.replace('## 16. Counter-Evidence', rng_spec + '\n## 16. Counter-Evidence')

# 7. exact per-file record-count specification
record_counts = '''
## 1. The World at a Glance (v2.1)

Rather than a single "total events" count, the generator expects exactly these record counts:

```json
{
  "expected_record_counts": {
    "persons": 55,
    "networks": 3,
    "organizations": 16,
    "phones": 42,
    "vehicles": 18,
    "accounts": 24,
    "properties": 8,
    "devices": 11,

    "cdrs": 385,
    "transactions": 50,
    "surveillance_reports": 12,
    "vehicle_sightings": 8,
    "intelligence_reports": 5,
    "criminal_history_records": 6,
    "property_transfers": 3
  }
}
```
'''
content = re.sub(r'## 1\. The World at a Glance.*?(?=## 2\.)', record_counts + '\n', content, flags=re.DOTALL)

# 8. corrected epistemic-status wording
content = content.replace('Indisputable real-world fact', 'Known truth within the synthetic world, used only as the validation answer key. (Hidden from production pipeline)')

# Account co-ownership
content = content.replace('Amit transfers money to joint account PNB-****8877', 'Amit and Harish are explicit co-holders of account PNB-****8877. Amit transfers money to this joint account')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully.')
