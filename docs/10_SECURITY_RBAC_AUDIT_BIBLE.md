# 10 — Security, RBAC & Audit Bible
**Version**: 1.0 | **Date**: 2026-08-29

---

## 1. Authentication vs Authorization

**Authentication** (who you are): handled by an external provider (Keycloak/Auth0).
**Authorization** (what you can do): handled by CIVIX (`civix_user`, `case_access`, PostgreSQL RLS).

The `civix.civix_user` table contains only investigative identity. No passwords, tokens, or secrets. (ADR-010)

---

## 2. Role Hierarchy

| Role | Description |
|---|---|
| `ADMIN` | Full system access, user management |
| `SUPERVISOR` | Can access all cases in their jurisdiction, approve hypotheses |
| `INVESTIGATOR` | Full read/write on assigned cases |
| `ANALYST` | AI-assisted analysis, cannot create hypotheses |
| `FORENSIC_EXAMINER` | Access to forensic/medical evidence only |
| `LEGAL_OFFICER` | Access to legal restriction management |
| `READ_ONLY` | Read access only, cannot write or export |

---

## 3. Case-Level Access Control

Case access is granular. A user may be INVESTIGATOR on Case A and READ_ONLY on Case B.

```
civix.case_access:
  case_id → investigative_case
  user_id → civix_user
  permission_level: READ | WRITE | ADMIN
  granted_by → civix_user
  granted_at, valid_until
  is_revoked, revoked_by, revoked_at
```

### 3.1 PostgreSQL RLS Integration

RLS policies on sensitive tables use `case_access`:
```sql
-- Example RLS policy on evidence_instance
CREATE POLICY case_access_policy ON civix.evidence_instance
  USING (
    case_id IN (
      SELECT case_id FROM civix.case_access
      WHERE user_id = current_setting('civix.user_id')::UUID
        AND is_revoked = FALSE
        AND (valid_until IS NULL OR valid_until > now())
    )
  );
```

### 3.2 Global Entity Exposure (ADR-028 & ADR-029)

While `civix.entity` is globally canonical and lacks DB-level RLS, API exposure is restricted:
- **Read (ADR-028)**: `GET /entities/{entity_id}` must manually enforce that the user can only retrieve an entity if it is associated with at least one case they are authorized to access (via `case_entity_role`). Unassociated entities must remain invisible.
- **Modify (ADR-029)**: `POST /identity/resolve` modifies global identity state and thus requires `SUPERVISOR` or `ADMIN` authorization. An `INVESTIGATOR` cannot execute a global identity merge/split.

### 3.3 Investigative Lead Disposition (ADR-032)

Unlike Identity Resolution, an Investigative Lead is a case-scoped workflow state.
- **Authorization**: A user must have `WRITE` access to the specific case (via `civix.case_access`). Therefore, a case-authorized `INVESTIGATOR`, `SUPERVISOR`, or `ADMIN` may dispose of a lead.
- **Isolation**: The actor must explicitly possess access to the `case_id` to which the lead belongs. Cross-case disposition attempts must be rejected with information-hiding semantics (404 Not Found).

---

## 4. Clearance Levels

Users have a `clearance_level` (UNCLASSIFIED, RESTRICTED, CONFIDENTIAL, SECRET).
Sources and evidence may have a classification level.

Rule: A user may not access evidence with a higher classification than their clearance.

STATUS: OPEN DECISION — the exact enforcement mechanism (RLS vs application layer) is not yet decided.

---

## 5. Audit Log

`civix.audit_event` is append-only.

A PostgreSQL trigger prevents any UPDATE or DELETE:
```sql
CREATE OR REPLACE FUNCTION civix.prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_event is immutable — UPDATE and DELETE are prohibited';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_immutability
BEFORE UPDATE OR DELETE ON civix.audit_event
FOR EACH ROW EXECUTE FUNCTION civix.prevent_audit_modification();
```

Every significant action (READ of sensitive evidence, hypothesis status change, identity resolution, restriction, tombstone) creates an `audit_event` row.

---

## 6. Legal Restrictions & Expungement

```
civix.legal_restriction:
  target: entity OR evidence_artifact (not both null)
  restriction_type: EXPUNGED | SEALED | JUVENILE_PROTECTED | ...
  effective_range: TSTZRANGE
  scope: FULL_RECORD | IDENTITY_ONLY | CONTENT_ONLY | ANALYTICAL_ONLY
  status: ACTIVE | LIFTED | EXPIRED
```

### 6.1 Expungement Flow

1. Legal order received → `legal_restriction(type=EXPUNGED, status=ACTIVE)` created
2. `audit_event(TOMBSTONE_ISSUED)` created
3. PostgreSQL trigger writes `outbox(action=TOMBSTONE, entity_id=X)`
4. CDC consumer reads outbox → Neo4j `MATCH (n {entity_id: X}) DETACH DELETE n`
5. RLS policy makes the PostgreSQL row invisible to standard queries
6. The PostgreSQL row is physically retained (for legal record) but invisible via RLS
7. Derived analytics (hypotheses, leads) that depended on the expunged entity are flagged for re-evaluation via `data_quality_issue`

### 6.2 Sealed vs Expunged

| Type | PostgreSQL | Neo4j | ML Training |
|---|---|---|---|
| SEALED | Invisible via RLS (retained) | Node marked restricted (not deleted) | Excluded |
| EXPUNGED | Invisible via RLS (retained) | Node physically DETACH DELETEd | Excluded |

---

## 7. Confidential Informant Protection

Sources with `is_identity_protected = TRUE` (e.g., intelligence_reports.json with source="Confidential Informant"):
- `source.source_handler_id` = the assigned handler's user_id
- Only the handler and ADMIN/SUPERVISOR can see the source's identity
- Intelligence derived from this source may be shared (as assertions) without revealing the source
- STATUS: OPEN DECISION — exact RLS policy for protected sources

---

## 8. Cross-Case Information Sharing

`civix.case_link` controls what can be shared between cases:
- `REFERENCE_ONLY`: Target case sees the lead text, not the underlying evidence
- `ASSERTIONS_ONLY`: Target case sees assertions but not evidence artifacts
- `FULL_EVIDENCE`: Target case gets full evidence access

An investigator can see a shared lead only if they have access to the target case.
