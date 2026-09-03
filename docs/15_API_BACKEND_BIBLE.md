# 15 — API & Backend Bible
**Version**: 1.1 | **Date**: 2026-08-31 | **Status**: Architecture formally DECIDED and implemented

---

> [!NOTE]
> This document captures what IS decided about the API/Backend and explicitly marks what is NOT yet decided.
> Do not implement the backend until architecture is finalized here.

---

## 1. What Is Decided

- Backend must enforce RLS by setting `civix.current_user_id` per session/request
- JWT tokens from the external auth provider are validated by the backend (not the database)
- Backend must NOT write directly to Neo4j — all graph writes go through the outbox
- Backend must NOT expose raw source_record data to the frontend — epistemic pipeline governs what is surfaced
- AI-generated leads must include explainability fields and MUST be explicitly persisted to `civix.investigative_lead` targeting a specific entity (ADR-026)
- All sensitive operations must write to `audit_event`
- `GET /entities/{entity_id}` MUST enforce API-level authorization ensuring the entity is associated with an accessible case (ADR-028)

## 2. Open Decisions

| Decision | Options | Status |
|---|---|---|
| Backend language/framework | Python / FastAPI | CLOSED (ADR-023) |
| ORM | SQLAlchemy AsyncSession | CLOSED (ADR-024) |
| API style | REST | CLOSED (Implemented in Phase 7 Task 1) |
| Async vs sync | Async (asyncio) | CLOSED (Implemented in Phase 7 Task 1) |
| Message broker for CDC | Kafka, Redis Streams, pg_notify | STATUS: OPEN DECISION |

## 3. API Surface (Minimum Required for SIH Demo)

Regardless of framework, the API must expose at minimum:

| Endpoint | Purpose |
|---|---|
| `POST /cases` | Create investigative case |
| `GET /cases/{id}` | Get case details + entities |
| `GET /cases/{id}/hypotheses` | List hypotheses for case |
| `POST /cases/{id}/hypotheses` | Create hypothesis (human only) |
| `GET /cases/{id}/leads` | List persisted investigative leads for case |
| `POST /cases/{id}/leads/generate` | Execute ML generation and persist leads (ADR-026) |
| `POST /cases/{id}/leads/{id}/disposition` | Dispose a lead (confirm/reject) |
| `GET /entities/{id}` | Get entity details + relationships (requires case authorization per ADR-028) |
| `POST /identity/resolve` | Trigger identity resolution decision (requires SUPERVISOR or ADMIN per ADR-029) |
| `GET /cases/{case_id}/graph` | Get Neo4j neighbors for visualization (Authoritative Contract per ADR-027) |
| `POST /ingest/cdr` | Ingest CDR batch |
| `POST /ingest/transaction` | Ingest transaction batch |
| `GET /search` | Full-text + attribute search across entities |

### 3.1 Identity Resolution Contract (ADR-031)

The canonical contract for `POST /identity/resolve` (which requires `SUPERVISOR` or `ADMIN` per ADR-029) is domain-faithful and supports both candidate-driven and manual resolutions:

**Request Schema**:
```json
{
  "source_identity_id": "UUID",
  "person_id": "UUID or null",
  "candidate_id": "UUID or null",
  "decision": "ACCEPTED | REJECTED",
  "decision_notes": "string"
}
```

**Rules**:
- `source_identity_id` is REQUIRED.
- `candidate_id` is OPTIONAL.
- `person_id` is REQUIRED when `decision = ACCEPTED`.
- `person_id` MUST be NULL when `decision = REJECTED`.
- `decision_notes` is REQUIRED for every human decision.
- The API must support both candidate-driven and manually initiated identity resolution.
- The API must not require an `identity_candidate` to exist.
- The response must represent the newly created persistent `identity_resolution`.

### 3.2 Lead Disposition Contract (ADR-032)

The canonical contract for `POST /api/v1/cases/{case_id}/leads/{lead_id}/disposition` represents an explicit workflow action.

**Request Schema**:
```json
{
  "status": "OPEN | IN_PROGRESS | CONFIRMED | FALSE_POSITIVE | CLOSED | DEFERRED",
  "disposition_notes": "string"
}
```

**Rules**:
- The API is an explicit workflow action (not a generic PATCH).
- The actor must be an `INVESTIGATOR`, `SUPERVISOR`, or `ADMIN` with write access to the specific case.
- The `lead_id` must belong to the supplied `case_id`. Cross-case access must return standard information hiding response (404 Not Found).
- Idempotency: If the lead is already in the requested status, return 200 OK without mutating the row or duplicating the audit event.
- Invalid state transitions must return 409 Conflict.
- The PostgreSQL row update and `audit_event` insertion must occur atomically in a single transaction.
- Concurrency: The transaction must acquire a pessimistic lock (`SELECT ... FOR UPDATE`) on the lead row before validating the state transition.
- No direct Neo4j interaction is permitted; standard CDC handles projection.

## 4. Required for Phase 8 Design

Before implementing the backend, this document must be extended with:
- Authentication middleware spec
- Session management spec
- Rate limiting spec
- Error response format
- Pagination strategy
- Background job management (for ML runs, outbox processing)
