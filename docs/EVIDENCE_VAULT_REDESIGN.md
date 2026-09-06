# CIVIX 2.0 — Case Evidence Vault Redesign Audit & Mapping

**Date:** September 2026  
**Status:** AUDIT COMPLETED — PROCEEDING TO IMPLEMENTATION PLAN

---

## 1. Executive Audit Findings

| Audit Question | System Answer | Details / Implementation |
|---|---|---|
| **A. File Previewing** | **YES** | Served via `/api/v1/evidence/artifacts/{artifact_id}/content` (FileResponse streaming). |
| **B. Download Endpoint** | **YES** | Binary stream with original filename via `/api/v1/evidence/artifacts/{artifact_id}/content`. |
| **C. Upload Endpoint** | **YES** | `POST /api/v1/cases/{case_id}/evidence/upload` accepts `file`, `acquisition_method`, `acquisition_context`. |
| **D. Supported MIME Types** | **EXTENSIVE** | `image/jpeg`, `image/png`, `image/webp`, `image/gif`, `application/pdf`, `video/mp4`, `audio/mp3`, `audio/wav`, `text/plain`, binary fallbacks. |
| **E. Available Metadata** | **RICH** | `artifact_id`, `instance_id`, `original_filename`, `mime_type`, `file_size_bytes`, `processing_status`, `created_at`, `sha256_hash`, `storage_uri`, `evidence_type`, `evidence_title`, `acquired_by`, `acquisition_method`, `media_metadata`. |
| **F. Authenticated URLs** | **YES** | FastAPI endpoints enforce JWT authentication (`AuthenticatedCivixUser`) and RLS (`case_access`). |
| **G. Thumbnail Strategy** | **NATIVE / HYBRID** | Images use native object-fit cover with `loading="lazy"`; video/audio/PDF use file-type specific restrained previews. |
| **H. Storage Engine** | **CONTENT-ADDRESSED** | Local filesystem at `c:\data\civix_demo\evidence_store` with SHA-256 deduplication. |
| **I. Reusable Viewers** | **NEW / ENHANCED** | Modular Evidence Viewer panel / modal with tabbed details, media preview canvas, chain of custody, and download actions. |

---

## 2. Feature Mapping Matrix

| DATA SOURCE | UI FEATURE | EXISTING API / COMPONENT |
|---|---|---|
| `GET /api/v1/cases/{case_id}/evidence` | Vault Header & Counter | `evidenceList.length` (authoritative count) |
| `EvidenceListItem[]` | Evidence Grid Cards | Responsive 4–5 card grid in `CaseEvidenceVault.tsx` |
| `/api/v1/evidence/artifacts/{artifact_id}/content` | Image Previews | Native `<img>` with `object-fit: cover` and lazy loading |
| Artifact MIME type `video/*` | Video Previews | Thumbnail / poster frame + play indicator |
| Artifact MIME type `audio/*` | Audio Previews | Audio waveform / player style preview |
| Artifact MIME type `application/pdf` | PDF / Document Previews | Document icon + PDF metadata preview |
| Client-side filter on `evidenceList` | Search & Filters | Search (title, filename, artifact_id, mime_type), Type filter, Status filter, Sort order |
| `POST /api/v1/cases/{case_id}/evidence/upload` | Add Evidence Modal | File picker + drag & drop + optional acquisition metadata |
| `GET /api/v1/cases/{case_id}/evidence/{artifact_id}` | Evidence Viewer Modal / Drawer | Right slide-out panel / modal with media canvas, metadata, chain of custody, and actions |
| `/api/v1/evidence/artifacts/{artifact_id}/content` | Authenticated Download | Direct browser download / Blob trigger with preserved filename |

---

## 3. Safety & Integrity Guarantees

- **PostgreSQL & Neo4j Schemas**: 0% schema modifications required.
- **Hero & Golden Cases**: 100% immutable and protected. Verified with `scripts/hero_protection.py`.
- **Chain of Custody**: Preserved using actual DB fields (`acquired_by`, `acquisition_method`, `created_at`, `sha256_hash`).
- **No Manufactured Data**: Real artifact records used exclusively; fallback quiet states rendered when unsupported.
