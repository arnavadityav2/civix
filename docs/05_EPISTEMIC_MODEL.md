# 05 — Epistemic Model Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE

> [!IMPORTANT]
> The epistemic pipeline is the most critical CIVIX design invariant. Collapsing any layer is a critical architecture defect.

---

## 1. The Pipeline

```
EXTERNAL WORLD
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ SOURCE                                                      │
│ An external agency or system that provided data.            │
│ Examples: Jio Telecom, SBI Bank, Ajmer Police, CCTV-Node-7  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ SOURCE_RECORD                                               │
│ An immutable receipt of one data payload from a source.     │
│ One CDR row = one source_record.                            │
│ Immutable: corrections supersede, never update.             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EVIDENCE (EvidenceArtifact + EvidenceInstance)              │
│ The deduplicated artifact AND its case-scoped context.      │
│ One artifact may appear in multiple cases.                  │
│ Chain of custody lives here.                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌──────────────────────┐   ┌─────────────────────────────────┐
│ OBSERVATION          │   │ EXTRACTION                      │
│ Directly recorded    │   │ AI/NLP/CV-derived inference.    │
│ fact. No inference.  │   │ Has ai_confidence score.        │
│ Human or sensor.     │   │ Tied to analysis_run.           │
└──────────┬───────────┘   └──────────────┬──────────────────┘
           │                              │
           └──────────────┬───────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ EVENT                                                       │
│ A real-world occurrence hub. Contains ONLY timing+type.    │
│ NO entity FKs on event itself.                              │
│ Entities connect via event_participant.                     │
│ occurred_at is a TSTZRANGE (not scalar — uncertainty OK).   │
└──────────────────────────┬──────────────────────────────────┘
                           │ (via provenance)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ASSERTION                                                   │
│ A structured claim: Subject → Predicate → Object/Value      │
│ Contains epistemic_status (belief in this specific claim).  │
│ Does NOT contain stance toward any hypothesis.              │
│ Predicate MUST come from controlled predicate_enum.         │
│ One assertion may participate in multiple hypothesis evals. │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ HYPOTHESIS_SUPPORT                                          │
│ Directional relationship: does Assertion A support/         │
│ contradict/neutralize Hypothesis H?                         │
│ STANCE: SUPPORT | CONTRADICT | NEUTRAL | INCONCLUSIVE       │
│ weight: relative evidentiary weight                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ HYPOTHESIS                                                  │
│ An investigative theory under evaluation.                   │
│ Created by human investigators only.                        │
│ Confirmed only by human (DB CHECK constraint enforces this).│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ INVESTIGATIVE_LEAD                                          │
│ An actionable tip generated from hypotheses.                │
│ May be AI-generated but must be human-reviewed.             │
│ Disposition must be recorded (confirmed/false_positive).    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ INVESTIGATION_TASK                                          │
│ A specific human action to perform.                         │
│ Outcome must be recorded for audit.                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Assertion vs HypothesisSupport — Critical Distinction

| Concept | Table | Field | Meaning |
|---|---|---|---|
| "Is this S-P-O claim true?" | `assertion` | `epistemic_status` | POSSIBLE / PROBABLE / CONFIRMED / REFUTED / INCONCLUSIVE |
| "Does this claim help a specific hypothesis?" | `hypothesis_support` | `stance` | SUPPORT / CONTRADICT / NEUTRAL / INCONCLUSIVE |

**Example**:
- Assertion A1: "P-01 CALLED P-02 at 14:33:22 on Aug 13" → `epistemic_status = CONFIRMED`
- Hypothesis H1: "P-01 and P-02 coordinate drug deliveries via phone"
- Hypothesis H2: "The Aug 13 activity spike was due to a family emergency (exculpatory)"
- `hypothesis_support(A1 → H1, stance=SUPPORT, weight=0.7)`
- `hypothesis_support(A1 → H2, stance=NEUTRAL, weight=0.3)`

One assertion. Two different stances. Impossible if stance lived on assertion.

---

## 3. Event Participants (N-Ary Events)

Events have no entity FKs. All entity relationships go through `event_participant`.

**Call Event (CALL)**:
```
event(event_id=E1, event_type=CALL, occurred_at=[14:33:22, 14:35:47])
  ├── event_participant(E1, CALLER, source_identity: "9876543210")
  ├── event_participant(E1, CALLEE, source_identity: "9123456789")
  ├── event_participant(E1, CELL_TOWER, location: CELL-17)
  ├── event_participant(E1, PING_SOURCE, device: IMEI-868...)
```

**Property Mutation Event (resolves H4)**:
```
event(event_id=E7, event_type=PROPERTY_MUTATION, occurred_at=[2026-06-10, 2026-06-10])
  ├── event_participant(E7, PREVIOUS_OWNER, person: P-14 "Kamla Bai")
  ├── event_participant(E7, NEW_OWNER, person: P-12 "Sunita Agarwal")
  ├── event_participant(E7, TARGET_PROPERTY, property: Khasra-45)
  ├── event_participant(E7, TARGET_PROPERTY, property: Khasra-46)  [if applicable]
  └── event_participant(E7, REGISTRAR, location: "Ajmer Revenue Office")
```

---

## 4. Exculpatory Evidence

Exculpatory evidence is NOT a special case. It uses the same pipeline:

1. Evidence artifact: alibi photograph with timestamp
2. Observation: "P-03 was at Hospital X on Aug 13 at 14:30"
3. Assertion: `P-03 ALIBI_CONFIRMED_AT Hospital-X, valid_from=14:30, valid_to=17:00`
4. hypothesis_support: `(alibi assertion) CONTRADICTS (hypothesis that P-03 committed crime at 14:45)`

The system MUST surface this. An investigator who fails to represent it creates a corrupt hypothesis weight profile.

---

## 5. Forbidden Pipeline Shortcuts

| Shortcut | Why Forbidden |
|---|---|
| `Source → Assertion` (skipping evidence/observation) | Loses provenance and audit trail |
| `Extraction → Hypothesis` (skipping assertion) | Conflates inference with theory |
| `Assertion.stance = CONTRADICT` | Assertion has no stance |
| `EntityCluster → Assertion` | EntityCluster is mutable; assertions must target stable SourceIdentity/Person |
| `AI creates Hypothesis` | Hypotheses require human creation (DB CHECK) |
| `AI confirms Hypothesis` | Confirmation requires human sign-off (DB CHECK) |
| `Free-text predicate` | predicate must come from predicate_enum |

---

## 6. Provenance Risk Computation

Provenance risk is computed dynamically, never stored.

```sql
-- Pseudocode for provenance risk view
WITH RECURSIVE provenance_chain AS (
  SELECT provenance_id, source_id, source_type
  FROM civix.provenance
  WHERE derived_id = $assertion_id
  UNION ALL
  ...
)
SELECT MAX(severity) AS provenance_risk
FROM civix.data_quality_issue dqi
JOIN provenance_chain pc ON pc.source_id = dqi.affected_entity_id
WHERE dqi.status IN ('OPEN', 'ACKNOWLEDGED')
```

When a data_quality_issue is resolved, the risk score drops automatically — no cascading writes.

---

## 7. Investigative Leads (ADR-032)

Investigative Leads follow a strictly governed state machine:

| FROM | TO | Status |
|---|---|---|
| OPEN | IN_PROGRESS | AUTHORIZED |
| OPEN | CLOSED | AUTHORIZED |
| OPEN | FALSE_POSITIVE | AUTHORIZED |
| IN_PROGRESS | CONFIRMED | AUTHORIZED |
| IN_PROGRESS | FALSE_POSITIVE | AUTHORIZED |
| IN_PROGRESS | DEFERRED | AUTHORIZED |
| DEFERRED | IN_PROGRESS | AUTHORIZED |
| CONFIRMED | (Any) | FORBIDDEN (Terminal) |
| CLOSED | (Any) | FORBIDDEN (Terminal) |
| FALSE_POSITIVE | (Any) | FORBIDDEN (Terminal) |

Reopening terminal states is NOT supported in V1. If further investigation is required after a terminal Lead, a new Lead must be created to maintain strict audit chains.
