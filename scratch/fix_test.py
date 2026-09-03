with open(r'c:\Users\ARNAV ADITYA\Desktop\civix 2.0\tests\api\test_leads.py', 'r') as f:
    lines = f.readlines()

# find where `@pytest.fixture` starts for `setup_lead`
start_idx = -1
for i, line in enumerate(lines):
    if line.startswith('@pytest.fixture') and 'setup_lead' in lines[i+1]:
        start_idx = i
        break

# find where `assert "ai_confidence" in leads[0]` starts
end_idx = -1
for i, line in enumerate(lines):
    if 'assert "ai_confidence" in leads[0]' in line and i > start_idx:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    test_leads_original_end = lines[end_idx:]
    test_leads_top = lines[:start_idx]
    
    with open(r'c:\Users\ARNAV ADITYA\Desktop\civix 2.0\tests\api\test_leads.py', 'w') as f:
        f.writelines(test_leads_top)
        f.writelines([
            '        assert "lead_id" in leads[0]\n',
            '        assert "target_entity_id" in leads[0]\n'
        ])
        f.writelines(test_leads_original_end)

with open(r'c:\Users\ARNAV ADITYA\Desktop\civix 2.0\scratch\draft_test_leads_disposition.py', 'r') as f:
    draft = f.readlines()

# strip imports from draft
import_end = 0
for i, line in enumerate(draft):
    if line.startswith('@pytest.fixture'):
        import_end = i
        break

with open(r'c:\Users\ARNAV ADITYA\Desktop\civix 2.0\tests\api\test_leads.py', 'a') as f:
    f.writelines(draft[import_end:])
