import json
import re

mock = {
    "schema_version": "1.0",
    "entities": [
        {"local_id": "E001", "type": "PERSON", "canonical_name": "Rajesh Kumar Verma", "aliases": ["Rajesh Verma"], "attributes": {"date_of_birth": "1984-03-12", "gender": "MALE", "nationality": "IND"}, "confidence": 0.95, "source_spans": [{"page": 1, "text_snippet": "Name: Rajesh Kumar Verma"}]},
        {"local_id": "E002", "type": "PERSON", "canonical_name": "Ananya Singh", "aliases": [], "attributes": {"gender": "FEMALE"}, "confidence": 0.92, "source_spans": [{"page": 1, "text_snippet": "Complainant: Ananya Singh"}]},
        {"local_id": "E003", "type": "PERSON", "canonical_name": "Suresh Babu Yadav", "aliases": ["Suresh Yadav"], "attributes": {"gender": "MALE"}, "confidence": 0.90, "source_spans": [{"page": 1, "text_snippet": "Victim: Suresh Babu Yadav"}]},
        {"local_id": "E004", "type": "VEHICLE", "canonical_name": "RJ14-CB-2847", "aliases": ["white Maruti Swift"], "attributes": {"registration_number": "RJ14-CB-2847", "make": "Maruti", "model": "Swift", "color": "white", "vehicle_type": "CAR"}, "confidence": 0.97, "source_spans": [{"page": 1, "text_snippet": "white Maruti Swift"}]},
        {"local_id": "E005", "type": "ORGANIZATION", "canonical_name": "Verma Traders Private Limited", "aliases": ["Verma Traders"], "attributes": {"org_type": "COMPANY", "registration_number": "U52190RJ2015PTC047921"}, "confidence": 0.94, "source_spans": [{"page": 1, "text_snippet": "Verma Traders Private Limited"}]},
        {"local_id": "E006", "type": "LOCATION", "canonical_name": "Godown No. 7, Sanganer Industrial Area, Jaipur", "aliases": [], "attributes": {"address": "Godown No. 7, Sanganer Industrial Area, Jaipur, Rajasthan"}, "confidence": 0.93, "source_spans": [{"page": 1, "text_snippet": "Godown No. 7"}]},
        {"local_id": "E007", "type": "LOCATION", "canonical_name": "45-B Gandhi Nagar Jaipur", "aliases": ["45-B, Gandhi Nagar"], "attributes": {"address": "45-B, Gandhi Nagar, Jaipur, Rajasthan"}, "confidence": 0.88, "source_spans": [{"page": 1, "text_snippet": "45-B, Gandhi Nagar"}]}
    ],
    "relationships": [
        {"subject_local_id": "E001", "predicate": "OWNS", "object_local_id": "E004", "confidence": 0.95, "source_spans": [{"page": 1, "text_snippet": "registered to Rajesh Kumar Verma"}]},
        {"subject_local_id": "E001", "predicate": "EMPLOYED_BY", "object_local_id": "E005", "confidence": 0.93, "source_spans": [{"page": 1, "text_snippet": "proprietor of Verma Traders"}]},
        {"subject_local_id": "E001", "predicate": "SEEN_AT", "object_local_id": "E006", "confidence": 0.94, "source_spans": [{"page": 1, "text_snippet": "entering the godown"}]},
        {"subject_local_id": "E003", "predicate": "RESIDED_AT", "object_local_id": "E007", "confidence": 0.88, "source_spans": [{"page": 1, "text_snippet": "Permanent Residence: 45-B"}]}
    ],
    "temporal_facts": [
        {"event_description": "Rajesh Kumar Verma observed at Godown", "event_date": "2026-06-15", "event_time": "23:45:00", "temporal_precision": "MINUTE", "involved_entity_local_ids": ["E001", "E006"], "source_spans": [{"page": 1, "text_snippet": "witnessed at approximately 11:45 PM"}]}
    ]
}

m_str = json.dumps(mock, indent=4)
# In gemini_client.py
f1 = 'civix_api/services/nlp/gemini_client.py'
with open(f1, 'r', encoding='utf-8') as f:
    c1 = f.read()
c1 = re.sub(r'MOCK_FIR_001_EXTRACTION = json\.dumps\(\{.*?\}\)', 'MOCK_FIR_001_EXTRACTION = json.dumps(' + m_str + ')', c1, flags=re.DOTALL)
with open(f1, 'w', encoding='utf-8') as f:
    f.write(c1)

# In e2e_test_round2a.py
f2 = 'scratch/e2e_test_round2a.py'
with open(f2, 'r', encoding='utf-8') as f:
    c2 = f.read()
c2 = re.sub(r'MOCK_FIR_001_EXTRACTION = json\.dumps\(\{.*?\}\n    \]\n\)', 'MOCK_FIR_001_EXTRACTION = json.dumps(' + m_str + ')\n', c2, flags=re.DOTALL)

# Also fix the fallback pattern if the previous one didn't match
c2 = re.sub(r'MOCK_FIR_001_EXTRACTION = json\.dumps\(\{.*?\)\n', 'MOCK_FIR_001_EXTRACTION = json.dumps(' + m_str + ')\n', c2, flags=re.DOTALL)

# Revert my hardcoded checks back to original
c2 = c2.replace("'Ravi Kumar', 'Suresh Singh', 'Amit'", "'Rajesh Kumar Verma', 'Ananya Singh', 'Suresh Babu Yadav'")
c2 = c2.replace("'XYZ Transport Co.'", "'Verma Traders Private Limited'")

with open(f2, 'w', encoding='utf-8') as f:
    f.write(c2)
print('Done!')
