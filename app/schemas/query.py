from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryLogBase(BaseModel):
    """Base schema for query log data."""
    query_text: str = Field(..., description="The SQL query text")
    query_hash: str = Field(..., description="Hash of the query for identification")
    db_user: Optional[str] = Field(None, description="Database user who executed the query")
    database_name: Optional[str] = Field(None, description="Database name")
    total_exec_time: float = Field(..., description="Total execution time in milliseconds")
    mean_exec_time: float = Field(..., description="Mean execution time in milliseconds")
    calls: int = Field(..., description="Number of times the query was executed")


class QueryLogCreate(QueryLogBase):
    """Schema for creating a new query log entry."""
    pass


class QueryLogResponse(QueryLogBase):
    """Schema for query log response."""
    id: UUID
    collected_at: datetime
    
    class Config:
        from_attributes = True


class QueryLogList(BaseModel):
    """Schema for list of query logs."""
    queries: list[QueryLogResponse]
    total: int
    page: int
    size: int


class SlowQueryResponse(BaseModel):
    """Schema for slow query response with additional metrics."""
    id: UUID
    query_text: str
    query_hash: str
    mean_exec_time: float
    calls: int
    total_exec_time: float
    collected_at: datetime
    is_slow: bool = Field(..., description="Whether this query is considered slow")
    
    class Config:
        from_attributes = True 