from pydantic import BaseModel
from typing import Dict, List, Optional

class GraphResponse(BaseModel):
    """Response model for the graph/linked list representation"""
    graph: Dict[str, List[str]]
    metadata: Optional[Dict] = None

    class Config:
        # Exclude None values from the response
        exclude_none = True

class GraphMetadata(BaseModel):
    """Metadata about the generated graph"""
    total_nodes: int
    total_connections: int
    lines_included: List[str]
    intersection_points_count: int
    generated_at: str