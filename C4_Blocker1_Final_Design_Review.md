# C4 Blocker 1 Final Design Review
**Status**: DRAFT / UNIMPLEMENTED
**Scope**: Blocker 1 (Neha Coordinator) identity resolution contract

---

## 1. Is phone-only matching intentionally part of the approved C2 identity-resolution contract?
**No.** The authoritative `06_IDENTITY_RESOLUTION_BIBLE.md` and the existing C2 implementation (`entity_resolver.py`) strictly avoid single-signal matching. The approved rules (01-04) all require either an exact normalized name match or an explicit alias match as the primary anchor, supplemented by corroborating signals (phone, account, vehicle, org). A phone-only match was deliberately excluded.

## 2. Does the approved C2 design permit a candidate based on a single phone signal without corroborating name/account/vehicle/org evidence?
**No.** The deterministic engine's design requires multi-factor correlation to generate an `identity_candidate`. Generating a candidate based solely on a single phone number violates the conservative matching philosophy intended to prevent identity contamination.

## 3. What false-positive risk does RULE_05_PHONE_ONLY introduce?
A **severe false-positive risk**. In investigative datasets (e.g., CDRs, intelligence reports), phone numbers are frequently shared. A phone-only rule would aggressively merge unrelated individuals sharing a family phone, corporate pool device, cartel burner phone, or re-assigned SIM card. This contradicts the system's core tenet: *"CIVIX must never conflate uncertain identity resolution with established fact."*

## 4. Does the existing C2 API/architecture distinguish generation vs. acceptance vs. final resolution?
**Yes.** The architecture maintains strict separation:
- **Deterministic Candidate Generation:** Executed by `entity_resolver.py` rules to create `civix.identity_candidate` rows.
- **Investigator Acceptance:** Handled via the API (`POST /api/v1/identity/resolve`), which requires `SUPERVISOR` or `ADMIN` RBAC.
- **Final Identity Resolution:** The creation of the immutable `civix.identity_resolution` record and subsequent Neo4j CDC projection, executed *only* after explicit HITL authorization.

## 5. Can the C4 path be demonstrated using the EXISTING C2 contract without adding a new deterministic rule?
**YES.** 
The existing identity resolution API (`POST /api/v1/identity/resolve`) explicitly defines `candidate_id` as `Optional[UUID] = None`. This means the API contract intentionally supports **manually initiated identity resolution** without a preexisting deterministic candidate. 

To demonstrate the C4 path for Blocker 1:
1. Ingest "Neha Coordinator" as a `source_identity` (fixing the Golden World ingestion bug).
2. Because no deterministic rule matches, no candidate is generated.
3. In the C4 test (`test_c4_remediation.py`), simulate a `SUPERVISOR` manually invoking `POST /api/v1/identity/resolve` to link the `source_identity` to `Neha Gupta` (justified by their manual review of the shared phone number in the UI).
4. The API will successfully create the `identity_resolution` row.
5. The Neo4j projector will create the `RESOLVES_TO` edge.
6. The C3 deterministic engine will successfully traverse the multi-hop path to generate the lead.

## 6. Why a phone-only rule is NOT required
A phone-only deterministic rule is an unnecessary expansion of C2. The CIVIX architecture expects gaps in deterministic logic to be filled by human intelligence. Testing the manual resolution flow explicitly validates the intended Human-in-the-Loop (HITL) fallback mechanism without compromising the conservative deterministic engine.

## 7. RULE_05_PHONE_ONLY specifics
**N/A.** The rule is not genuinely required and is formally rejected as a design change. 

---

### Conclusion & Final Recommendation for Blocker 1
**Classification:** DATA PRESERVATION + FIX INGESTION + CONTRACT EXTENSION
1. **Fix Ingestion:** Update `ingest_golden_world.py` to ingest "Neha Coordinator" as a `source_identity`.
2. **Do NOT expand C2:** Abandon the proposal to add `RULE_05_PHONE_ONLY`.
3. **Extend C4 Test:** Add an API call to `test_c4_remediation.py` to manually resolve the `source_identity` to `Neha Gupta` via `POST /api/v1/identity/resolve` (without a `candidate_id`) prior to evaluating the C3 path. 

*No changes have been implemented yet. Awaiting authorization.*
