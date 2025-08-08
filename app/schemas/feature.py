from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryFeatureBase(BaseModel):
    """Base schema for query feature data."""
    query_id: UUID = Field(..., description="ID of the associated query")
    num_joins: int = Field(default=0, description="Number of JOIN clauses")
    has_select_star: bool = Field(default=False, description="Whether query uses SELECT *")
    has_where_clause: bool = Field(default=False, description="Whether query has WHERE clause")
    num_subqueries: int = Field(default=0, description="Number of subqueries")
    scan_types: Optional[list[str]] = Field(None, description="Types of scans used in execution plan")
    indexed_tables_pct: Optional[float] = Field(None, description="Percentage of tables with indexes")
    avg_table_size_mb: Optional[float] = Field(None, description="Average table size in MB")
    is_slow_query: bool = Field(default=False, description="Whether this is considered a slow query")
    complexity_score: Optional[float] = Field(None, description="Query complexity score")


class QueryFeatureCreate(QueryFeatureBase):
    """Schema for creating a new query feature entry."""
    pass


class QueryFeatureResponse(QueryFeatureBase):
    """Schema for query feature response."""
    id: UUID
    
    class Config:
        from_attributes = True


class FeatureVector(BaseModel):
    """Schema for ML feature vector."""
    query_id: UUID
    features: dict[str, float] = Field(..., description="Feature vector for ML model")
    target: Optional[float] = Field(None, description="Target value for training (execution time)")
    
    class Config:
        from_attributes = True 