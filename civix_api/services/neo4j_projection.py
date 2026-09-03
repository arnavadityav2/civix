import logging
import json
from neo4j import Session
from neo4j.exceptions import TransientError

logger = logging.getLogger(__name__)

ALLOWED_ENTITY_LABELS = {
    'person': 'Person',
    'source_identity': 'Identity',
    'phone_number': 'PhoneNumber',
    'sim': 'SIM',
    'device': 'Device',
    'financial_account': 'FinancialAccount',
    'vehicle': 'Vehicle',
    'property': 'Property',
    'organization': 'Organization',
    'network': 'Network',
    'location': 'Location',
    'investigative_case': 'Case',
    'fir': 'FIR',
    'event': 'Event',
    'assertion': 'Assertion',
    'hypothesis': 'Hypothesis',
    'investigative_lead': 'Lead'
}

class Neo4jProjectionService:
    def __init__(self):
        pass

    def project(self, session: Session, action: str, entity_type: str, payload: dict, seq_no: int):
        """
        Projects a single outbox event to Neo4j, ensuring idempotency via last_seq_no.
        """
        if action == 'UPSERT_NODE':
            if entity_type == 'assertion':
                self._upsert_assertion(session, payload, seq_no)
            elif entity_type == 'event_participant':
                self._upsert_event_participant(session, payload, seq_no)
            elif entity_type == 'hypothesis_support':
                self._upsert_hypothesis_support(session, payload, seq_no)
            elif entity_type == 'identity_resolution':
                self._upsert_identity_resolution(session, payload, seq_no)
            elif entity_type == 'investigative_lead':
                self._upsert_investigative_lead(session, payload, seq_no)
            else:
                self._upsert_node(session, entity_type, payload, seq_no)
        elif action == 'TOMBSTONE_NODE':
            self._tombstone_node(session, entity_type, payload, seq_no)
        elif action == 'DEACTIVATE_NODE':
            self._deactivate_node(session, entity_type, payload, seq_no)
        elif action == 'UPSERT_EDGE':
            if entity_type == 'case_entity_role':
                self._upsert_case_entity_role(session, payload, seq_no)
            elif entity_type == 'identity_candidate':
                self._upsert_identity_candidate(session, payload, seq_no)
            # Other edge types handled as UPSERT_NODE events by generic triggers
        elif action == 'DEACTIVATE_EDGE':
            if entity_type == 'case_entity_role':
                self._deactivate_case_entity_role(session, payload, seq_no)
            elif entity_type == 'identity_candidate':
                self._deactivate_identity_candidate(session, payload, seq_no)
        elif action == 'CCTV_OBSERVATION_CREATED':
            self._upsert_cctv_observation(session, payload, seq_no)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _get_identity_info(self, entity_type: str, payload: dict):
        entity_type_lower = entity_type.lower()
        if entity_type_lower not in ALLOWED_ENTITY_LABELS:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        label = ALLOWED_ENTITY_LABELS[entity_type_lower]
        ident_key = 'entity_id'
        
        # Override PK logic based on label
        if label == 'Case':
            ident_key = 'case_id'
        elif label == 'FIR':
            ident_key = 'fir_id'
        elif label == 'Event':
            ident_key = 'event_id'
        elif label == 'Assertion':
            ident_key = 'assertion_id'
        elif label == 'Hypothesis':
            ident_key = 'hypothesis_id'
        elif label == 'Lead':
            ident_key = 'lead_id'
            
        ident_val = payload.get(ident_key) or payload.get('entity_id')
        if not ident_val:
            raise ValueError(f"Missing identity for {entity_type}")
            
        return label, ident_key, ident_val

    def _upsert_node(self, session: Session, entity_type: str, payload: dict, seq_no: int):
        label, ident_key, ident_val = self._get_identity_info(entity_type, payload)
        
        query = f"""
        MERGE (n:{label} {{{ident_key}: $ident_val}})
        SET n._lock = true
        WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET n += $payload, n.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, ident_val=ident_val, seq_no=seq_no, payload=payload).single()
        if not record:
            raise TransientError(f"Missing endpoints for {label}")
        logger.debug(f"UPSERT_NODE {label} {ident_val} (seq {seq_no})")

    def _upsert_assertion(self, session: Session, payload: dict, seq_no: int):
        assertion_id = payload.get('assertion_id')
        subject_id = payload.get('subject_entity_id')
        object_id = payload.get('object_entity_id')
        object_type = payload.get('object_entity_type')
        
        if not all([assertion_id, subject_id, object_id, object_type]):
            raise ValueError("Missing critical identifiers for assertion")
            
        object_type_lower = object_type.lower()
        if object_type_lower not in ALLOWED_ENTITY_LABELS:
            raise ValueError(f"Unknown object entity type: {object_type}")
            
        object_label = ALLOWED_ENTITY_LABELS[object_type_lower]
        
        _, object_ident_key, _ = self._get_identity_info(object_type, {
            'entity_id': object_id,
            'case_id': object_id,
            'fir_id': object_id,
            'event_id': object_id,
            'assertion_id': object_id,
            'hypothesis_id': object_id,
            'lead_id': object_id
        })
        
        query = f"""
        MATCH (i) WHERE (i:Identity OR i:Person OR i:Organization OR i:Vehicle OR i:Location OR i:PhoneNumber OR i:SourceIdentity) AND (i.entity_id = $subject_id OR i.source_identity_id = $subject_id)
        MATCH (o:{object_label} {{{object_ident_key}: $object_id}})
        MERGE (a:Assertion {{assertion_id: $assertion_id}})
        SET a._lock = true
        
        WITH a, i, o, (a.last_seq_no IS NULL OR $seq_no > a.last_seq_no) AS should_apply
        
        OPTIONAL MATCH (a)<-[old_sub:ASSERTED_BY]-()
        WITH a, i, o, should_apply, collect(DISTINCT old_sub) AS old_subs
        
        OPTIONAL MATCH (a)-[old_obj:ASSERTS]->()
        WITH a, i, o, should_apply, old_subs, collect(DISTINCT old_obj) AS old_objs
        
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            FOREACH (sub IN [x IN old_subs WHERE x IS NOT NULL] | DELETE sub)
            FOREACH (obj IN [x IN old_objs WHERE x IS NOT NULL] | DELETE obj)
            SET a += $payload, a.last_seq_no = $seq_no
            CREATE (i)-[:ASSERTED_BY]->(a)
            CREATE (a)-[:ASSERTS]->(o)
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, assertion_id=assertion_id, subject_id=subject_id, object_id=object_id, seq_no=seq_no, payload=payload).single()
        if not record:
            raise TransientError("Missing endpoints for assertion projection")
        logger.debug(f"UPSERT_ASSERTION {assertion_id} (seq {seq_no})")

    def _upsert_event_participant(self, session: Session, payload: dict, seq_no: int):
        participant_id = payload.get('participant_id')
        event_id = payload.get('event_id')
        entity_id = payload.get('entity_id')
        entity_type = payload.get('entity_type')
        
        if not all([participant_id, event_id, entity_id, entity_type]):
            raise ValueError("Missing identifiers for event_participant")
            
        entity_type_lower = entity_type.lower()
        if entity_type_lower not in ALLOWED_ENTITY_LABELS:
            raise ValueError(f"Unknown target entity type: {entity_type}")
            
        target_label = ALLOWED_ENTITY_LABELS[entity_type_lower]
        _, target_ident_key, _ = self._get_identity_info(entity_type, {
            'entity_id': entity_id,
            'case_id': entity_id,
            'fir_id': entity_id,
            'event_id': entity_id,
            'assertion_id': entity_id,
            'hypothesis_id': entity_id,
            'lead_id': entity_id
        })
        
        query = f"""
        MATCH (e:Event {{event_id: $event_id}})
        MATCH (t:{target_label} {{{target_ident_key}: $entity_id}})
        MERGE (e)-[r:PARTICIPATED_AS {{participant_id: $participant_id}}]->(t)
        SET r._lock = true
        WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET r += $payload, r.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, participant_id=participant_id, event_id=event_id, entity_id=entity_id, seq_no=seq_no, payload=payload).single()
        if not record:
            raise TransientError("Missing endpoints for event_participant projection")
        logger.debug(f"UPSERT_EVENT_PARTICIPANT {participant_id} (seq {seq_no})")

    def _upsert_hypothesis_support(self, session: Session, payload: dict, seq_no: int):
        support_id = payload.get('support_id')
        hypothesis_id = payload.get('hypothesis_id')
        assertion_id = payload.get('assertion_id')
        
        if not all([support_id, hypothesis_id, assertion_id]):
            raise ValueError("Missing identifiers for hypothesis_support")
            
        query = f"""
        MATCH (a:Assertion {{assertion_id: $assertion_id}})
        MATCH (h:Hypothesis {{hypothesis_id: $hypothesis_id}})
        MERGE (a)-[r:HAS_STANCE {{support_id: $support_id}}]->(h)
        SET r._lock = true
        WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET r += $payload, r.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, support_id=support_id, hypothesis_id=hypothesis_id, assertion_id=assertion_id, seq_no=seq_no, payload=payload).single()
        if not record:
            raise TransientError("Missing endpoints for hypothesis_support projection")
        logger.debug(f"UPSERT_HYPOTHESIS_SUPPORT {support_id} (seq {seq_no})")
        
    def _upsert_identity_resolution(self, session: Session, payload: dict, seq_no: int):
        status = payload.get('status')
        if status == 'REJECTED':
            logger.debug(f"UPSERT_IDENTITY_RESOLUTION (seq {seq_no}) - REJECTED ignored per ADR-031")
            return
            
        resolution_id = payload.get('resolution_id')
        source_id = payload.get('source_identity_id')
        person_id = payload.get('resolved_person_id')
        
        if not all([resolution_id, source_id, person_id]):
            raise ValueError("Missing identifiers for identity_resolution")
            
        query = f"""
        MATCH (i:Identity {{entity_id: $source_id}})
        MATCH (p:Person {{entity_id: $person_id}})
        MERGE (i)-[r:RESOLVES_TO {{resolution_id: $resolution_id}}]->(p)
        SET r._lock = true
        WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET r += $payload, r.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, resolution_id=resolution_id, source_id=source_id, person_id=person_id, seq_no=seq_no, payload=payload).single()
        if not record:
            raise TransientError("Missing endpoints for identity_resolution projection")
        logger.debug(f"UPSERT_IDENTITY_RESOLUTION {resolution_id} (seq {seq_no})")

    def _upsert_investigative_lead(self, session: Session, payload: dict, seq_no: int):
        lead_id = payload.get('lead_id')
        if not lead_id:
            raise ValueError("Missing lead_id for investigative_lead")
            
        status = payload.get('status')
        if status in ('CLOSED', 'FALSE_POSITIVE'):
            query = """
            OPTIONAL MATCH (n:Lead {lead_id: $lead_id})
            WITH n, CASE WHEN n IS NOT NULL AND (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) THEN [1] ELSE [] END AS should_apply
            FOREACH (_ IN should_apply |
                DETACH DELETE n
            )
            RETURN true AS projection_processed
            """
            session.run(query, lead_id=lead_id, seq_no=seq_no)
            logger.debug(f"UPSERT_INVESTIGATIVE_LEAD {lead_id} (seq {seq_no}) - DELETED/EXCLUDED due to status {status}")
            return

        # C3: Project explanation_status, feature_vector_version, finding_count
        # Deterministic findings themselves are stored in PostgreSQL, not Neo4j.
        # Neo4j receives only summary attributes — not raw findings JSONB (too large).
        # NO SAME AS or RESOLVES TO edges are created here.
        authorized_payload = {
            'lead_id': lead_id,
            'case_id': payload.get('case_id'),
            'priority': payload.get('priority'),
            'status': status,
            'ai_confidence': payload.get('ai_confidence'),
            # C3 additions
            'explanation_status': payload.get('explanation_status'),
            'feature_vector_version': payload.get('feature_vector_version'),
            'finding_count': payload.get('finding_count', 0),
        }
        
        query = """
        MERGE (n:Lead {lead_id: $lead_id})
        SET n._lock = true
        WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET n += $authorized_payload, n.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, lead_id=lead_id, seq_no=seq_no, authorized_payload=authorized_payload).single()
        if not record:
            raise TransientError("Missing endpoints for lead projection")
        logger.debug(f"UPSERT_INVESTIGATIVE_LEAD {lead_id} expl_status={authorized_payload.get('explanation_status')} (seq {seq_no})")



    def _upsert_case_entity_role(self, session: Session, payload: dict, seq_no: int):
        """
        Projects a case_entity_role row as a (Case)-[:HAS_ROLE]->(Entity) relationship.

        Idempotency: MERGE on role_id ensures no duplicate relationships are created
        on retries. SET is guarded by seq_no so out-of-order events cannot downgrade
        a newer state.

        The entity node must already exist in Neo4j (projected via entity outbox trigger).
        If the entity node is not yet projected, the MATCH will fail and the CDCWorker
        will receive a TransientError, which causes a retry without dead-lettering.

        PostgreSQL remains the source of truth. This is a read-model projection only.
        """
        role_id   = payload.get('role_id')
        case_id   = payload.get('case_id')
        entity_id = payload.get('entity_id')
        role      = payload.get('role')
        role_basis = payload.get('role_basis')  # nullable

        if not all([role_id, case_id, entity_id, role]):
            raise ValueError(f"Missing required fields for case_entity_role projection: {payload}")

        # We use MATCH for both endpoints to guarantee they already exist in Neo4j.
        # If either is missing, the MATCH fails → TransientError → CDCWorker retries.
        # This prevents HAS_ROLE relationships from referencing non-existent nodes.
        query = """
        MATCH (c:Case {case_id: $case_id})
        MATCH (e {entity_id: $entity_id})
        MERGE (c)-[r:HAS_ROLE {role_id: $role_id}]->(e)
        SET r._lock = true
        WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET r.role       = $role,
                r.role_basis = $role_basis,
                r.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(
            query,
            role_id=role_id,
            case_id=case_id,
            entity_id=entity_id,
            role=role,
            role_basis=role_basis,
            seq_no=seq_no
        ).single()
        if not record:
            raise TransientError(
                f"HAS_ROLE projection failed: Case {case_id} or Entity {entity_id} not found in Neo4j. "
                f"The entity may not yet be projected. This event will be retried."
            )
        logger.debug(f"UPSERT_CASE_ENTITY_ROLE role_id={role_id} case={case_id} entity={entity_id} role={role} (seq {seq_no})")

    def _deactivate_case_entity_role(self, session: Session, payload: dict, seq_no: int):
        """
        Removes the (Case)-[:HAS_ROLE {role_id}]->(Entity) relationship from Neo4j
        when the corresponding case_entity_role row is soft-deleted (tx_end set).

        Uses OPTIONAL MATCH so that if the relationship is already absent (e.g. a
        duplicate deactivation event), the operation is a no-op rather than an error.
        Idempotency is preserved.
        """
        role_id = payload.get('role_id')
        if not role_id:
            raise ValueError(f"Missing role_id for DEACTIVATE_EDGE case_entity_role: {payload}")

        query = """
        OPTIONAL MATCH ()-[r:HAS_ROLE {role_id: $role_id}]->()
        WITH r, (r IS NOT NULL AND (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no)) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            DELETE r
        )
        RETURN true AS projection_processed
        """
        session.run(query, role_id=role_id, seq_no=seq_no)
        logger.debug(f"DEACTIVATE_CASE_ENTITY_ROLE role_id={role_id} (seq {seq_no})")

    def _upsert_identity_candidate(self, session: Session, payload: dict, seq_no: int):
        candidate_id = payload.get('candidate_id')
        source_id = payload.get('source_identity_id')
        person_id = payload.get('proposed_person_id')
        rule_id = payload.get('matching_rule_id', 'LEGACY')
        signals = payload.get('deterministic_signals', [])

        if not all([candidate_id, source_id, person_id]):
            raise ValueError(f"Missing required fields for identity_candidate projection: {payload}")

        import json
        query = """
        MATCH (i:Identity {entity_id: $source_id})
        MATCH (p:Person {entity_id: $person_id})
        MERGE (i)-[r:CANDIDATE_FOR {candidate_id: $candidate_id}]->(p)
        SET r._lock = true
        WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET r.rule = $rule_id,
                r.signals = $signals_json,
                r.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(
            query,
            candidate_id=candidate_id,
            source_id=source_id,
            person_id=person_id,
            rule_id=rule_id,
            signals_json=json.dumps(signals),
            seq_no=seq_no
        ).single()
        if not record:
            raise TransientError(
                f"CANDIDATE_FOR projection failed: Identity {source_id} or Person {person_id} not found in Neo4j. "
                f"The entity may not yet be projected. This event will be retried."
            )
        logger.debug(f"UPSERT_IDENTITY_CANDIDATE candidate={candidate_id} (seq {seq_no})")

    def _deactivate_identity_candidate(self, session: Session, payload: dict, seq_no: int):
        candidate_id = payload.get('candidate_id')
        if not candidate_id:
            raise ValueError(f"Missing candidate_id for DEACTIVATE_EDGE identity_candidate: {payload}")

        query = """
        OPTIONAL MATCH ()-[r:CANDIDATE_FOR {candidate_id: $candidate_id}]->()
        WITH r, (r IS NOT NULL AND (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no)) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            DELETE r
        )
        RETURN true AS projection_processed
        """
        session.run(query, candidate_id=candidate_id, seq_no=seq_no)
        logger.debug(f"DEACTIVATE_IDENTITY_CANDIDATE candidate={candidate_id} (seq {seq_no})")

    def _tombstone_node(self, session: Session, entity_type: str, payload: dict, seq_no: int):
        label, ident_key, ident_val = self._get_identity_info(entity_type, payload)
        
        query = f"""
        MATCH (n:{label} {{{ident_key}: $ident_val}})
        SET n._lock = true
        WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET n.visibility_status = 'TOMBSTONED', 
                n.tombstoned_at = $tombstoned_at, 
                n.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, ident_val=ident_val, seq_no=seq_no, tombstoned_at=payload.get('tombstoned_at')).single()
        if not record:
            raise TransientError(f"Missing endpoints for {label} tombstone")
        logger.debug(f"TOMBSTONE_NODE {label} {ident_val} (seq {seq_no})")

    def _deactivate_node(self, session: Session, entity_type: str, payload: dict, seq_no: int):
        label, ident_key, ident_val = self._get_identity_info(entity_type, payload)
        
        query = f"""
        MATCH (n:{label} {{{ident_key}: $ident_val}})
        SET n._lock = true
        WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET n.visibility_status = 'RESTRICTED', 
                n.restricted_at = $restricted_at, 
                n.last_seq_no = $seq_no
        )
        RETURN true AS projection_processed
        """
        record = session.run(query, ident_val=ident_val, seq_no=seq_no, restricted_at=payload.get('restricted_at')).single()
        if not record:
            raise TransientError(f"Missing endpoints for {label} deactivate")
        logger.debug(f"DEACTIVATE_NODE {label} {ident_val} (seq {seq_no})")

    def _upsert_cctv_observation(self, session: Session, payload: dict, seq_no: int):
        observation_id = payload.get('observation_id')
        case_id = payload.get('case_id')
        target_vehicle_id = payload.get('target_vehicle_id')
        camera_id = payload.get('camera_id')
        signal_class = payload.get('signal_class')
        
        if not all([observation_id, case_id, target_vehicle_id, camera_id]):
            raise ValueError(f"Missing identifiers for CCTV_OBSERVATION_CREATED: {payload}")
            
        query = f"""
        MATCH (c:Case {{case_id: $case_id}})
        MATCH (v:Vehicle {{entity_id: $target_vehicle_id}})
        MERGE (o:CCTVObservation {{observation_id: $observation_id}})
        SET o._lock = true
        WITH o, c, v, (o.last_seq_no IS NULL OR $seq_no > o.last_seq_no) AS should_apply
        FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
            SET o += $payload, o.last_seq_no = $seq_no
            MERGE (c)-[:CONTAINS_EVIDENCE]->(o)
            MERGE (o)-[:IDENTIFIES_VEHICLE]->(v)
        )
        RETURN true AS projection_processed
        """
        record = session.run(
            query,
            observation_id=observation_id,
            case_id=case_id,
            target_vehicle_id=target_vehicle_id,
            seq_no=seq_no,
            payload=payload
        ).single()
        
        if not record:
            raise TransientError("Missing endpoints for CCTVObservation projection")
        logger.debug(f"CCTV_OBSERVATION_CREATED {observation_id} (seq {seq_no})")
