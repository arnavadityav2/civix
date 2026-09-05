from neo4j import GraphDatabase

case_id = "1346a86d-267a-a635-9d62-e34c76ecd24f"
accessible_case_ids = ["1346a86d-267a-a635-9d62-e34c76ecd24f", "bb1a67a5-525b-48f8-f793-d60c23c514ca"]

driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "password"))

depth = 1
query = f"""
MATCH path = (c:Case {{case_id: $case_id}})-[*0..{depth}]-(n)
WHERE all(node IN nodes(path) WHERE 
    node.tx_end IS NULL
    AND coalesce(node.visibility_status, 'ACTIVE') = 'ACTIVE'
    AND (
        (node.case_id IS NULL AND node.authorized_case_ids IS NULL)
        OR (node.case_id IS NOT NULL AND node.case_id IN $accessible_case_ids)
        OR (node.authorized_case_ids IS NOT NULL AND any(cid IN node.authorized_case_ids WHERE cid IN $accessible_case_ids))
    )
)
AND all(rel IN relationships(path) WHERE
    rel.tx_end IS NULL AND rel.superseded_by IS NULL
)
WITH collect(path) AS paths

// 1. Gather distinct valid nodes up to the node_limit
UNWIND (CASE WHEN size(paths) > 0 THEN paths ELSE [null] END) AS p
UNWIND (CASE WHEN p IS NOT NULL THEN nodes(p) ELSE [] END) AS node
WITH collect(DISTINCT node)[0..$node_limit] AS valid_nodes, paths

// 2. Extract relationships safely without dropping rows if empty
UNWIND (CASE WHEN size(paths) > 0 THEN paths ELSE [null] END) AS p
UNWIND (CASE WHEN p IS NOT NULL THEN relationships(p) ELSE [] END) AS rel
WITH valid_nodes, collect(DISTINCT rel) AS raw_rels
WITH valid_nodes, [r IN raw_rels WHERE r IS NOT NULL AND startNode(r) IN valid_nodes AND endNode(r) IN valid_nodes][0..$rel_limit] AS valid_rels

RETURN valid_nodes, valid_rels
"""

with driver.session() as session:
    res = session.run(query, case_id=case_id, accessible_case_ids=accessible_case_ids, node_limit=100, rel_limit=200)
    rec = res.single()
    if rec:
        print("FIXED QUERY RESULTS:")
        print("  Valid Nodes:", len(rec['valid_nodes']), [n.labels for n in rec['valid_nodes']])
        print("  Valid Rels:", len(rec['valid_rels']), [r.type for r in rec['valid_rels']])
    else:
        print("Still returned None!")

driver.close()
