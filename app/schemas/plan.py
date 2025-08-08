from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionPlanBase(BaseModel):
    """Base schema for execution plan data."""
    query_id: UUID = Field(..., description="ID of the associated query")
    plan_json: Dict[str, Any] = Field(..., description="JSON representation of the EXPLAIN plan")
    total_cost: Optional[float] = Field(None, description="Total cost from the execution plan")
    actual_time: Optional[float] = Field(None, description="Actual execution time from ANALYZE")
    plan_depth: Optional[int] = Field(None, description="Depth of the execution plan tree")
    plan_type: Optional[str] = Field(None, description="Type of EXPLAIN (e.g., 'EXPLAIN', 'EXPLAIN ANALYZE')")


class ExecutionPlanCreate(ExecutionPlanBase):
    """Schema for creating a new execution plan entry."""
    pass


class ExecutionPlanResponse(ExecutionPlanBase):
    """Schema for execution plan response."""
    id: UUID
    
    class Config:
        from_attributes = True


class PlanAnalysis(BaseModel):
    """Schema for plan analysis results."""
    query_id: UUID
    plan_id: UUID
    total_cost: float
    actual_time: float
    plan_depth: int
    scan_types: list[str] = Field(default_factory=list, description="Types of scans used")
    join_types: list[str] = Field(default_factory=list, description="Types of joins used")
    has_sequential_scan: bool = Field(..., description="Whether plan uses sequential scans")
    has_index_scan: bool = Field(..., description="Whether plan uses index scans")
    estimated_rows: Optional[int] = Field(None, description="Estimated number of rows")
    actual_rows: Optional[int] = Field(None, description="Actual number of rows")
    
    class Config:
        from_attributes = True 