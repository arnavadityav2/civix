# CIVIX 2.0 — Cases Page Intelligence Redesign Audit & Mapping

**Date:** September 2026  
**Status:** APPROVED WITH REQUIRED CORRECTIONS — READY FOR FRONTEND IMPLEMENTATION

---

## 1. Executive Data Source Audit & Mapping

| UI ELEMENT | DATA SOURCE | DERIVATION | FALLBACK |
|---|---|---|---|
| **NEEDS ATTENTION Count** | `GET /api/v1/cases/registry` items | `items.filter(c => c.priority === 'CRITICAL' || c.status === 'OPEN' || c.lead_count > 2).length` | `0` |
| **CROSS-CASE CONNECTIONS Count** | `GET /api/v1/cases/registry` items | `items.filter(c => c.provenance === 'GOLDEN' || c.case_type === 'MULTI_CASE' || c.entity_count >= 6).length` | `0` |
| **UNRESOLVED LEADS Count** | `GET /api/v1/cases/registry` items | `items.reduce((sum, c) => sum + (c.lead_count || 0), 0)` | `0` |
| **TOTAL / ACTIVE / CRITICAL / GOLDEN COUNTS** | `GET /api/v1/cases/registry` summary | `summary.total_cases`, `summary.active_cases`, `summary.critical_cases`, `summary.golden_cases` | Authoritative summary values |
| **INTELLIGENCE SIGNALS Badge** | `CaseRegistryItem` (`lead_count`, `entity_count`, `provenance`, `priority`, `case_type`) | Deterministic, traceable signal generator:<br/>1. `lead_count > 0` &rarr; `● ${lead_count} unresolved lead${s}`<br/>2. `provenance === 'GOLDEN'` &rarr; `● Hero / Golden manifest case`<br/>3. `entity_count >= 5` &rarr; `● ${entity_count} connected entities`<br/>4. `case_type === 'FINANCIAL'` &rarr; `● Financial transaction overlap`<br/>5. `case_type === 'PROPERTY'` &rarr; `● Property network linkage`<br/>6. `case_type === 'MULTI_CASE'` &rarr; `● Multi-case syndicate overlap`<br/>7. `priority === 'CRITICAL'` &rarr; `● Critical priority investigation` | Quiet state (No badge shown if unsupported) |
| **SIGNAL INSPECTOR Side Panel** | Selected `CaseRegistryItem` attributes + underlying graph/lead record facts | Populating **WHY THIS CASE IS SURFACED**:<br/>- Source record / Entity / Lead breakdown<br/>- Deterministic signal rationale<br/>- Quick action routes (`OPEN GRAPH`, `OPEN CASE`) | "No active intelligence signal for this case" |
| **INVESTIGATIVE COVERAGE Visualization** | Registry summary & item totals | Mini NCR network/coverage canvas showing system case coverage (Cases, Entities, Locations, Evidence) | System-derived synthetic overlay |

---

## 2. Governance & Integrity Compliance Rules

1. **ZERO HARDCODED COUNTS:** All signals, metric counts, and card statistics are calculated dynamically from API data.
2. **TRACEABLE SIGNALS:** Every signal directly maps to real API data (`lead_count`, `entity_count`, `provenance`, `case_type`, `priority`).
3. **EXPLAINABILITY:** Clicking a signal opens the Signal Inspector explaining *WHY THIS CASE IS SURFACED*.
4. **NO FAKE AI:** Terminology strictly uses `CIVIX INTELLIGENCE`, `INVESTIGATIVE SIGNAL`, `MACHINE-ASSISTED ANALYSIS`. Zero robot icons, zero purple styling, zero fake confidence scores.
5. **APPROVED QUOTE:** `"DATA CLOSES CASES. INTELLIGENCE CONNECTS THE DOTS."` (No attribution to Delhi Police).
6. **NAVIGATION SEPARATION:** Row click navigates to `/cases/{caseId}`. Signal badge click opens the Signal Inspector.
7. **BACKEND SAFETY:** 0 database schema changes, 0 graph mutations, 0 hero case modifications.

---

## 3. Visual & Aesthetic Architecture

- **Theme Palette:** Deep navy command workstation (`#07090E` base, `#11141C` panel surface, `#1E2430` borders, `#3B82F6` blue accent, `#EF4444` red alert, `#E6B325` gold manifest badge).
- **Typography:** JetBrains Mono / Inter sans-serif mix with strict institutional uppercase headers and crisp micro-badges.
