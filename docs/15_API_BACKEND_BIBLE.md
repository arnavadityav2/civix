# 15 — API & Backend Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: OPEN DECISION — Architecture not yet designed

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
- AI-generated leads must include explainability fields
- All sensitive operations must write to `audit_event`

## 2. Open Decisions

| Decision | Options | Status |
|---|---|---|
| Backend language/framework | Python/FastAPI, Python/Django, Node.js | STATUS: OPEN DECISION |
| ORM | SQLAlchemy, Tortoise, Prisma, raw SQL | STATUS: OPEN DECISION |
| API style | REST, GraphQL, gRPC | STATUS: OPEN DECISION |
| Async vs sync | Async (asyncio) vs sync | STATUS: OPEN DECISION |
| Message broker for CDC | Kafka, Redis Streams, pg_notify | STATUS: OPEN DECISION |

## 3. API Surface (Minimum Required for SIH Demo)

Regardless of framework, the API must expose at minimum:

| Endpoint | Purpose |
|---|---|
| `POST /cases` | Create investigative case |
| `GET /cases/{id}` | Get case details + entities |
| `GET /cases/{id}/hypotheses` | List hypotheses for case |
| `POST /cases/{id}/hypotheses` | Create hypothesis (human only) |
| `GET /cases/{id}/leads` | List investigative leads |
| `POST /cases/{id}/leads/{id}/disposition` | Dispose a lead (confirm/reject) |
| `GET /entities/{id}` | Get entity details + relationships |
| `POST /identity/resolve` | Trigger identity resolution decision |
| `GET /graph/neighbors/{entity_id}` | Get Neo4j neighbors for visualization |
| `POST /ingest/cdr` | Ingest CDR batch |
| `POST /ingest/transaction` | Ingest transaction batch |
| `GET /search` | Full-text + attribute search across entities |

## 4. Required for Phase 8 Design

Before implementing the backend, this document must be extended with:
- Authentication middleware spec
- Session management spec
- Rate limiting spec
- Error response format
- Pagination strategy
- Background job management (for ML runs, outbox processing)
