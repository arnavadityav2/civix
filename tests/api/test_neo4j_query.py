import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi import status

from civix_api.services.neo4j_query import Neo4jQueryService
from civix_api.models.graph import GraphResponse
from neo4j.exceptions import TransientError, ClientError, ResultConsumedError
from fastapi.exceptions import HTTPException

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_neo4j_session():
    session = AsyncMock()
    return session

async def test_get_case_graph_valid_traversal(mock_neo4j_session):
    # Setup mock result
    mock_result = AsyncMock()
    
    mock_record = MagicMock()
    
    # Mock node
    mock_node = MagicMock()
    mock_node.element_id = "node1"
    mock_node.get.side_effect = lambda k: "case-123" if k == "case_id" else None
    mock_node.labels = ["Case"]
    mock_node.items.return_value = [("case_id", "case-123")]
    
    # Mock relationship
    mock_rel = MagicMock()
    mock_rel.element_id = "rel1"
    mock_rel.type = "INVOLVED_IN"
    mock_rel.items.return_value = []
    start_n = MagicMock()
    start_n.element_id = "node1"
    start_n.get.side_effect = lambda k: "case-123" if k == "case_id" else None
    end_n = MagicMock()
    end_n.element_id = "node2"
    end_n.get.side_effect = lambda k: "person-1" if k == "entity_id" else None
    mock_rel.nodes = [start_n, end_n]

    mock_record.get.side_effect = lambda key, default: [mock_node, end_n] if key == "valid_nodes" else [mock_rel]
    
    mock_result.single.return_value = mock_record
    mock_neo4j_session.run.return_value = mock_result

    accessible_case_ids = ["case-123", "case-456"]
    
    response = await Neo4jQueryService.get_case_graph(
        session=mock_neo4j_session,
        case_id="case-123",
        accessible_case_ids=accessible_case_ids,
        depth=1,
        node_limit=10,
        rel_limit=20
    )

    assert isinstance(response, GraphResponse)
    assert len(response.nodes) == 2
    assert response.nodes[0].id == "case-123"
    assert len(response.relationships) == 1
    assert response.relationships[0].start_node == "case-123"
    assert response.relationships[0].end_node == "person-1"

    # Verify session run parameters
    mock_neo4j_session.run.assert_called_once()
    args, kwargs = mock_neo4j_session.run.call_args
    query = args[0]
    params = args[1]
    
    # Verify the ACL is passed
    assert "accessible_case_ids" in params
    assert params["accessible_case_ids"] == accessible_case_ids
    assert params["node_limit"] == 10
    assert params["rel_limit"] == 20
    assert "timeout" in kwargs
    assert kwargs["timeout"] == 5.0
    
    # Verify the path filter exists in cypher
    assert "WHERE all(node IN nodes(path)" in query
    assert "node.tx_end IS NULL" in query
    assert "rel.tx_end IS NULL" in query
    assert "node.case_id IN $accessible_case_ids" in query
    assert "UNWIND relationships(p) AS rel" in query

async def test_get_case_graph_timeout_error(mock_neo4j_session):
    mock_neo4j_session.run.side_effect = TransientError("Timeout")
    
    with pytest.raises(HTTPException) as excinfo:
        await Neo4jQueryService.get_case_graph(
            session=mock_neo4j_session,
            case_id="case-123",
            accessible_case_ids=["case-123"],
            depth=1,
            node_limit=10,
            rel_limit=20
        )
    
    assert excinfo.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

async def test_get_case_graph_client_error(mock_neo4j_session):
    mock_neo4j_session.run.side_effect = ClientError("Bad Syntax")
    
    with pytest.raises(HTTPException) as excinfo:
        await Neo4jQueryService.get_case_graph(
            session=mock_neo4j_session,
            case_id="case-123",
            accessible_case_ids=["case-123"],
            depth=1,
            node_limit=10,
            rel_limit=20
        )
    
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST

async def test_get_case_graph_unexpected_error(mock_neo4j_session):
    mock_neo4j_session.run.side_effect = Exception("System Crash")
    
    with pytest.raises(HTTPException) as excinfo:
        await Neo4jQueryService.get_case_graph(
            session=mock_neo4j_session,
            case_id="case-123",
            accessible_case_ids=["case-123"],
            depth=1,
            node_limit=10,
            rel_limit=20
        )
    
    assert excinfo.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "System Crash" not in str(excinfo.value.detail) # Sanitized
