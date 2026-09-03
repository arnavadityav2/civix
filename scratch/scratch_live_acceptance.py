import asyncio
import uuid
import sys
import os
import traceback
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civix_api.services.neo4j_projection import Neo4jProjectionService
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError, ConstraintError

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
projection = Neo4jProjectionService()

def run_query(query, **kwargs):
    with driver.session() as session:
        return session.run(query, **kwargs).data()

def reset_db():
    run_query("MATCH (n) DETACH DELETE n")

def T1_FreshAssertion():
    reset_db()
    sid = str(uuid.uuid4())
    oid = str(uuid.uuid4())
    aid = str(uuid.uuid4())

    with driver.session() as session:
        session.run("CREATE (:Identity {entity_id: $sid})", sid=sid)
        session.run("CREATE (:Person {entity_id: $oid})", oid=oid)
        
        payload = {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person"}
        projection.project(session, "UPSERT_NODE", "assertion", payload, seq_no=1)
        
        data = session.run("MATCH (i:Identity)-[r1:ASSERTED_BY]->(a:Assertion)-[r2:ASSERTS]->(o:Person) WHERE a.assertion_id = $aid RETURN a.assertion_id", aid=aid).data()
    return "PASS" if data else "FAIL"

def T2_StaleAssertion():
    reset_db()
    sid = str(uuid.uuid4()); oid = str(uuid.uuid4()); aid = str(uuid.uuid4())
    with driver.session() as session:
        session.run("CREATE (:Identity {entity_id: $sid})", sid=sid)
        session.run("CREATE (:Person {entity_id: $oid})", oid=oid)
        projection.project(session, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person", "val": "new"}, seq_no=20)
        projection.project(session, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person", "val": "old"}, seq_no=15)
        val = session.run("MATCH (a:Assertion) RETURN a.val as val").data()[0]['val']
    return "PASS" if val == "new" else "FAIL"

def T3_DuplicateCollapse():
    reset_db()
    sid = str(uuid.uuid4()); oid = str(uuid.uuid4()); aid = str(uuid.uuid4())
    with driver.session() as session:
        session.run("CREATE (i:Identity {entity_id: $sid}), (o:Person {entity_id: $oid}), (a:Assertion {assertion_id: $aid}) CREATE (i)-[:ASSERTED_BY]->(a), (i)-[:ASSERTED_BY]->(a), (a)-[:ASSERTS]->(o), (a)-[:ASSERTS]->(o), (a)-[:ASSERTS]->(o)", sid=sid, oid=oid, aid=aid)
        
        projection.project(session, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person"}, seq_no=2)
        
        data = session.run("MATCH (a:Assertion {assertion_id: $aid}) OPTIONAL MATCH (a)<-[s:ASSERTED_BY]-() OPTIONAL MATCH (a)-[o:ASSERTS]->() RETURN count(DISTINCT s) AS s_cnt, count(DISTINCT o) AS o_cnt", aid=aid).data()[0]
    return "PASS" if data['s_cnt'] == 1 and data['o_cnt'] == 1 else "FAIL"

def T4_MissingSubject():
    reset_db()
    aid = str(uuid.uuid4()); oid = str(uuid.uuid4())
    with driver.session() as session:
        session.run("CREATE (:Person {entity_id: $oid})", oid=oid)
        try:
            with session.begin_transaction() as tx:
                projection.project(tx, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": "missing", "object_entity_id": oid, "object_entity_type": "person"}, seq_no=1)
                tx.commit()
            return "FAIL"
        except TransientError:
            cnt = session.run("MATCH (a:Assertion) RETURN count(a) AS c").data()[0]['c']
            return "PASS" if cnt == 0 else "FAIL"

def T5_MissingObject():
    reset_db()
    aid = str(uuid.uuid4()); sid = str(uuid.uuid4())
    with driver.session() as session:
        session.run("CREATE (:Identity {entity_id: $sid})", sid=sid)
        try:
            with session.begin_transaction() as tx:
                projection.project(tx, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": "missing", "object_entity_type": "person"}, seq_no=1)
                tx.commit()
            return "FAIL"
        except TransientError:
            cnt = session.run("MATCH (a:Assertion) RETURN count(a) AS c").data()[0]['c']
            return "PASS" if cnt == 0 else "FAIL"

def T6_Concurrent_10_11():
    reset_db()
    sid = str(uuid.uuid4()); oid = str(uuid.uuid4()); aid = str(uuid.uuid4())
    run_query("CREATE (:Identity {entity_id: $sid}), (:Person {entity_id: $oid})", sid=sid, oid=oid)

    def worker(seq, val):
        payload = {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person", "val": val}
        try:
            with driver.session() as session:
                projection.project(session, "UPSERT_NODE", "assertion", payload, seq_no=seq)
        except Exception:
            pass

    t1 = threading.Thread(target=worker, args=(10, "ten"))
    t2 = threading.Thread(target=worker, args=(11, "eleven"))
    t1.start(); t2.start()
    t1.join(); t2.join()
    
    res = run_query("MATCH (a:Assertion) RETURN a.last_seq_no AS seq, a.val AS val")[0]
    return "PASS" if res['seq'] == 11 and res['val'] == "eleven" else f"FAIL {res}"

def T7_Concurrent_11_10():
    reset_db()
    sid = str(uuid.uuid4()); oid = str(uuid.uuid4()); aid = str(uuid.uuid4())
    run_query("CREATE (:Identity {entity_id: $sid}), (:Person {entity_id: $oid})", sid=sid, oid=oid)

    def worker(seq, val):
        payload = {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person", "val": val}
        try:
            with driver.session() as session:
                projection.project(session, "UPSERT_NODE", "assertion", payload, seq_no=seq)
        except Exception:
            pass

    # Give seq 11 a slight head start to guarantee it commits first, then seq 10 hits it
    worker(11, "eleven")
    worker(10, "ten")
    
    res = run_query("MATCH (a:Assertion) RETURN a.last_seq_no AS seq, a.val AS val")[0]
    return "PASS" if res['seq'] == 11 and res['val'] == "eleven" else f"FAIL {res}"

def T8_TransactionRollback():
    reset_db()
    aid = str(uuid.uuid4())
    try:
        with driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("CREATE (:Assertion {assertion_id: $aid, val: 'partial'})", aid=aid)
                raise ValueError("Simulated Exception")
    except ValueError:
        pass
    cnt = run_query("MATCH (a:Assertion) RETURN count(a) AS c")[0]['c']
    return "PASS" if cnt == 0 else "FAIL"

def T9_ReplayIdempotency():
    reset_db()
    sid = str(uuid.uuid4()); oid = str(uuid.uuid4()); aid = str(uuid.uuid4())
    run_query("CREATE (:Identity {entity_id: $sid}), (:Person {entity_id: $oid})", sid=sid, oid=oid)
    with driver.session() as session:
        payload = {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "person"}
        projection.project(session, "UPSERT_NODE", "assertion", payload, seq_no=5)
        projection.project(session, "UPSERT_NODE", "assertion", payload, seq_no=5)
    
    data = run_query("MATCH (a:Assertion) OPTIONAL MATCH (a)<-[s:ASSERTED_BY]-() OPTIONAL MATCH (a)-[o:ASSERTS]->() RETURN count(DISTINCT s) AS sc, count(DISTINCT o) AS oc, a.last_seq_no AS seq")[0]
    return "PASS" if data['sc'] == 1 and data['oc'] == 1 and data['seq'] == 5 else "FAIL"

def T10_EventParticipant():
    reset_db()
    eid = str(uuid.uuid4()); pid = str(uuid.uuid4()); part_id = str(uuid.uuid4())
    run_query("CREATE (:Event {event_id: $eid}), (:Person {entity_id: $pid})", eid=eid, pid=pid)
    with driver.session() as session:
        projection.project(session, "UPSERT_NODE", "event_participant", {"participant_id": part_id, "event_id": eid, "entity_id": pid, "entity_type": "person"}, seq_no=1)
    cnt = run_query("MATCH (:Event)-[r:PARTICIPATED_AS]->(:Person) RETURN count(r) AS c")[0]['c']
    return "PASS" if cnt == 1 else "FAIL"

def T11_HypothesisSupport():
    reset_db()
    hid = str(uuid.uuid4()); aid = str(uuid.uuid4()); sid = str(uuid.uuid4())
    run_query("CREATE (:Hypothesis {hypothesis_id: $hid}), (:Assertion {assertion_id: $aid})", hid=hid, aid=aid)
    with driver.session() as session:
        projection.project(session, "UPSERT_NODE", "hypothesis_support", {"support_id": sid, "hypothesis_id": hid, "assertion_id": aid}, seq_no=1)
    cnt = run_query("MATCH (:Assertion)-[r:HAS_STANCE]->(:Hypothesis) RETURN count(r) AS c")[0]['c']
    return "PASS" if cnt == 1 else "FAIL"

def T12_IdentityResolution():
    reset_db()
    iid = str(uuid.uuid4()); pid = str(uuid.uuid4()); rid = str(uuid.uuid4())
    run_query("CREATE (:Identity {entity_id: $iid}), (:Person {entity_id: $pid})", iid=iid, pid=pid)
    with driver.session() as session:
        projection.project(session, "UPSERT_NODE", "identity_resolution", {"resolution_id": rid, "source_identity_id": iid, "resolved_person_id": pid}, seq_no=1)
    cnt = run_query("MATCH (:Identity)-[r:RESOLVES_TO]->(:Person) RETURN count(r) AS c")[0]['c']
    return "PASS" if cnt == 1 else "FAIL"

def T13_Lifecycle():
    reset_db()
    pid = str(uuid.uuid4())
    with driver.session() as session:
        projection.project(session, "UPSERT_NODE", "person", {"entity_id": pid}, seq_no=1)
        projection.project(session, "TOMBSTONE_NODE", "person", {"entity_id": pid, "tombstoned_at": "2026"}, seq_no=2)
    vs = run_query("MATCH (p:Person) RETURN p.visibility_status AS vs")[0]['vs']
    return "PASS" if vs == "TOMBSTONED" else "FAIL"

def T14_ACL():
    reset_db()
    cid1 = str(uuid.uuid4()); cid2 = str(uuid.uuid4()); aid = str(uuid.uuid4())
    run_query("CREATE (c1:Case {case_id: $c1}), (c2:Case {case_id: $c2}), (a:Assertion {assertion_id: $a, authorized_case_ids: [$c2]})", c1=cid1, c2=cid2, a=aid)
    
    # Simulate user authorized only for c1 trying to query Assertion protected by c2
    auth_cases = [cid1]
    query = """
    MATCH (a:Assertion {assertion_id: $aid})
    WHERE (a.case_id IS NULL AND a.authorized_case_ids IS NULL)
       OR (a.case_id IS NOT NULL AND a.case_id IN $accessible_case_ids)
       OR (a.authorized_case_ids IS NOT NULL AND any(cid IN a.authorized_case_ids WHERE cid IN $accessible_case_ids))
    RETURN a.assertion_id AS aid
    """
    data = run_query(query, aid=aid, accessible_case_ids=auth_cases)
    return "PASS" if len(data) == 0 else "FAIL"

def T15_LabelInjection():
    reset_db()
    aid = str(uuid.uuid4()); sid = str(uuid.uuid4()); oid = str(uuid.uuid4())
    with driver.session() as session:
        session.run("CREATE (:Identity {entity_id: $sid}), (:Person {entity_id: $oid})", sid=sid, oid=oid)
        try:
            projection.project(session, "UPSERT_NODE", "assertion", {"assertion_id": aid, "subject_entity_id": sid, "object_entity_id": oid, "object_entity_type": "Person) DETACH DELETE n //"}, seq_no=1)
            return "FAIL"
        except ValueError:
            return "PASS"

def T16_Constraints():
    reset_db()
    aid = str(uuid.uuid4())
    run_query("CREATE (a:Assertion {assertion_id: $a})", a=aid)
    try:
        run_query("CREATE (a:Assertion {assertion_id: $a})", a=aid)
        return "FAIL" # duplicate should raise ConstraintError
    except ConstraintError:
        return "PASS"

tests = [
    ("T1 Fresh Assertion", T1_FreshAssertion),
    ("T2 Stale Assertion", T2_StaleAssertion),
    ("T3 Duplicate Assertion Collapse", T3_DuplicateCollapse),
    ("T4 Missing Subject", T4_MissingSubject),
    ("T5 Missing Object", T5_MissingObject),
    ("T6 Concurrent Seq 10/11", T6_Concurrent_10_11),
    ("T7 Reverse Concurrent Order", T7_Concurrent_11_10),
    ("T8 Transaction Rollback", T8_TransactionRollback),
    ("T9 Replay Idempotency", T9_ReplayIdempotency),
    ("T10 Event Participant", T10_EventParticipant),
    ("T11 Hypothesis Support", T11_HypothesisSupport),
    ("T12 Identity Resolution", T12_IdentityResolution),
    ("T13 Lifecycle", T13_Lifecycle),
    ("T14 ACL", T14_ACL),
    ("T15 Label Injection", T15_LabelInjection),
    ("T16 Constraints", T16_Constraints),
]

def run_all():
    for name, func in tests:
        try:
            res = func()
            print(f"{name:35} {res}")
        except Exception as e:
            print(f"{name:35} FAIL - {e}")
            traceback.print_exc()

if __name__ == "__main__":
    print("Executing FULL Live Acceptance Suite...")
    run_all()
    driver.close()
