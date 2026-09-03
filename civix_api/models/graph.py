from pydantic import BaseModel, Field
from typing import List, Dict, Any

class GraphNode(BaseModel):
    id: str = Field(..., description="Internal or domain identifier for the node")
    labels: List[str] = Field(default_factory=list, description="List of labels applied to the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key-value properties of the node")

class GraphRelationship(BaseModel):
    id: str = Field(..., description="Internal or domain identifier for the relationship")
    type: str = Field(..., description="Relationship type (e.g. SUPPORTS, INVOLVED_IN)")
    start_node: str = Field(..., description="Identifier of the start node")
    end_node: str = Field(..., description="Identifier of the end node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key-value properties of the relationship")

class GraphResponse(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)
