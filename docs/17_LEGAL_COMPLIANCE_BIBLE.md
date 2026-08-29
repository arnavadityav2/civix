# 17 — Legal & Compliance Bible
**Version**: 1.0 | **Date**: 2026-08-29

---

## 1. India-Specific Legal Context

CIVIX operates in the Indian legal context. Key laws:

| Law | Relevance |
|---|---|
| IT Act 2000 (amended 2008) | Electronic evidence admissibility |
| DPDP Act 2023 | Digital Personal Data Protection — limits retention, requires purpose limitation |
| CrPC / BNSS 2023 | Criminal procedure — FIRs, warrant requirements |
| Evidence Act 1872 | Admissibility of electronic records (Section 65B) |
| Telegraph Act 1885 | Intercept authorizations (CDR data) |

STATUS: OPEN DECISION — legal review by qualified Indian legal counsel required before production deployment.

---

## 2. Data Retention

STATUS: OPEN DECISION — retention periods must be defined per data category.

Proposed (not yet decided):
| Category | Retention |
|---|---|
| CDR data | 7 years (per TRAI regulations) |
| Financial transactions | 10 years (per RBI) |
| FIR/case records | 30 years (criminal records) |
| Audit logs | 10 years |
| ML training data (synthetic) | Indefinite (not personal data) |

---

## 3. Expungement & Sealing

See `10_SECURITY_RBAC_AUDIT_BIBLE.md` Section 6 for the technical implementation.

Legal categories:
- **EXPUNGED**: Court-ordered destruction. PostgreSQL row retained for legal compliance; invisible via RLS; Neo4j node physically deleted.
- **SEALED**: Court-ordered restriction. Content inaccessible but existence acknowledgeable.
- **JUVENILE_PROTECTED**: Automatic restriction on records involving persons under 18.
- **COURT_RESTRICTED**: Specific court order restricting access to certain parties.

---

## 4. Juvenile Records

A person flagged as a juvenile at the time of the recorded event must have all their case records automatically subject to `JUVENILE_PROTECTED` restriction.

Rule: If `person.date_of_birth` + event date = age < 18, create `legal_restriction(JUVENILE_PROTECTED)`.

STATUS: OPEN DECISION — automatic enforcement mechanism (trigger vs application logic).

---

## 5. SIM Reassignment (India-Specific)

In India, mobile numbers are frequently reassigned after 90 days of inactivity.

A phone number is NOT a permanent identity.

The `sim_number_assignment` table with GIST temporal exclusion constraint correctly handles this.

See `08_SPATIOTEMPORAL_MODEL.md` and `12_SYNTHETIC_DATA_BIBLE.md` for related design.

---

## 6. Section 65B Certificate (Electronic Evidence)

For evidence to be admissible in Indian courts, electronic records require a Section 65B certificate from the IT Act.

The CIVIX evidence chain provides the necessary metadata for generating such certificates:
- `source` (originating system)
- `evidence_instance.acquisition_method`
- `evidence_instance.acquired_by` (officer who obtained it)
- `evidence_artifact.is_integrity_verified` (hash verification)
- `audit_event` trail

STATUS: OPEN DECISION — actual certificate generation workflow needs legal review.

---

## 7. Confidential Informant Protection

See `10_SECURITY_RBAC_AUDIT_BIBLE.md` Section 7.

Intelligence derived from protected sources may be used in assertions and hypotheses.
The source's identity is never exposed without proper authorization.
