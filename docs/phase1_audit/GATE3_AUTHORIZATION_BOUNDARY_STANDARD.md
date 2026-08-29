# GATE 3: AUTHORIZATION BOUNDARY STANDARD
Date: 2026-08-29

## Assertion Access
`assertion` table has `authorized_case_ids UUID[]`.
- Populated via DB trigger on `assertion_evidence` and `evidence_instance`.
- RLS Policy: `WHERE authorized_case_ids && (SELECT array_agg(case_id) FROM case_access WHERE user_id = current_user AND valid_until > now())`.
- Fails closed: If empty, invisible.\n