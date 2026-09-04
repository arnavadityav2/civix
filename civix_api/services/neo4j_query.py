import logging
from typing import List, Dict, Any, Tuple
from neo4j import AsyncSession
from neo4j.exceptions import ClientError, TransientError, ResultConsumedError
from fastapi import HTTPException, status

from ..models.graph import GraphNode, GraphRelationship, GraphResponse

logger = logging.getLogger(__name__)

class Neo4jQueryService:
    @staticmethod
    async def get_case_graph(
        session: AsyncSession,
        case_id: str,
        accessible_case_ids: List[str],
        depth: int,
        node_limit: int,
        rel_limit: int
    ) -> GraphResponse:
        """
        Executes a bounded graph traversal from a root case_id.
        Strictly enforces that every traversed node satisfies the ACL.
        """
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

        parameters = {
            "case_id": str(case_id),
            "accessible_case_ids": [str(c) for c in accessible_case_ids],
            "node_limit": node_limit,
            "rel_limit": rel_limit
        }

        def sanitize_properties(props: dict) -> dict:
            sanitized = {}
            for k, v in props.items():
                if hasattr(v, "iso_format"):
                    sanitized[k] = v.iso_format()
                elif hasattr(v, "to_native"):
                    sanitized[k] = str(v)
                else:
                    sanitized[k] = v
            return sanitized

        try:
            # 5.0 second timeout bound
            result = await session.run(query, parameters, timeout=5.0)
            record = await result.single()

            if not record:
                return GraphResponse(nodes=[], relationships=[])

            valid_nodes = record.get("valid_nodes", [])
            valid_rels = record.get("valid_rels", [])

            # Create a lookup mapping element_id to domain_id for the frontend
            element_to_domain = {}

            # Transform into Pydantic models
            graph_nodes = []
            for n in valid_nodes:
                if not n:
                    continue
                # For Neo4j < 5 element_id is used, else elementId.
                # neo4j python driver 5.x provides element_id property
                n_id = n.element_id
                
                # Determine domain ID if possible (for client mapping)
                # Fallback to internal element_id if standard entity_id/case_id/fir_id is absent
                domain_id = n.get("entity_id") or n.get("case_id") or n.get("fir_id") or n_id
                element_to_domain[n_id] = str(domain_id)
                
                graph_nodes.append(GraphNode(
                    id=str(domain_id),
                    labels=list(n.labels),
                    properties=sanitize_properties(dict(n.items()))
                ))

            graph_relationships = []
            for r in valid_rels:
                if not r:
                    continue
                r_id = r.element_id
                
                start_n = r.nodes[0]
                end_n = r.nodes[1]
                
                # Look up the domain identifiers using the mapping
                start_domain_id = element_to_domain.get(start_n.element_id, start_n.element_id)
                end_domain_id = element_to_domain.get(end_n.element_id, end_n.element_id)
                
                graph_relationships.append(GraphRelationship(
                    id=str(r_id),
                    type=r.type,
                    start_node=str(start_domain_id),
                    end_node=str(end_domain_id),
                    properties=sanitize_properties(dict(r.items()))
                ))

            return GraphResponse(nodes=graph_nodes, relationships=graph_relationships)

        except TransientError as e:
            logger.error(f"Neo4j Transient Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Graph database temporarily unavailable")
        except ClientError as e:
            logger.error(f"Neo4j Client Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph query")
        except ResultConsumedError as e:
            logger.error(f"Neo4j Result Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Graph result could not be processed")
        except Exception as e:
            logger.error(f"Neo4j Unexpected Error: {str(e)}")
            # Do not leak stack traces or raw Cypher
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal graph database error occurred")
