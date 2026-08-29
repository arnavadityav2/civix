# 16 — Frontend Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: OPEN DECISION

---

## 1. What Is Decided

- Frontend must NOT make direct Neo4j queries (go through backend API)
- Graph visualization is a required feature for SIH demo
- Case-level access must be enforced (only show entities/leads for user's cases)
- Exculpatory evidence must be prominently surfaced, not hidden
- AI confidence scores must be visible and understandable to investigators

## 2. Open Decisions

| Decision | Options | Status |
|---|---|---|
| Frontend framework | React, Next.js, Vue.js | STATUS: OPEN DECISION |
| Graph visualization library | Sigma.js, Vis.js, Cytoscape.js, D3 | STATUS: OPEN DECISION |
| UI component library | MUI, Ant Design, Shadcn | STATUS: OPEN DECISION |
| Map library | Leaflet, Mapbox, Google Maps | STATUS: OPEN DECISION |
| State management | Redux, Zustand, React Query | STATUS: OPEN DECISION |

## 3. Required UI Features (SIH Demo)

| Feature | Priority |
|---|---|
| Interactive entity graph (Neo4j visualization) | CRITICAL |
| Case dashboard (entities, hypotheses, leads) | CRITICAL |
| Timeline view (events over time) | HIGH |
| Map view (spatial entities, cell sectors, sightings) | HIGH |
| Search (person, vehicle, phone, property) | HIGH |
| Hypothesis creation and management | HIGH |
| Lead disposition workflow | HIGH |
| Evidence viewer (with provenance chain) | MEDIUM |
| Identity resolution workflow | MEDIUM |
| Audit log viewer (for admins) | MEDIUM |
