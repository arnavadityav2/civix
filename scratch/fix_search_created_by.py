with open('tests/api/test_search.py', 'r') as f:
    text = f.read()

text = text.replace("'jurisdiction', 'status', 'lead_investigator_id', 'opened_at')", "'jurisdiction', 'status', 'lead_investigator_id', 'opened_at', 'created_by')")
text = text.replace("'OPEN', :uid, now())", "'OPEN', :uid, now(), :uid)")

with open('tests/api/test_search.py', 'w') as f:
    f.write(text)

with open('tests/api/test_leads.py', 'r') as f:
    text = f.read()

text = text.replace("created_by)", ")")
text = text.replace(", :uid)", ")")

with open('tests/api/test_leads.py', 'w') as f:
    f.write(text)
