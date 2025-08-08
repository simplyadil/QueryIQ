from typing import Optional

from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ExecutionPlan(Base):
    """Model for storing parsed EXPLAIN execution plans."""
    
    __tablename__ = "execution_plans"
    
    # Foreign key to query log
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Plan data
    plan_json = Column(JSONB, nullable=False)
    
    # Performance metrics from plan
    total_cost = Column(Float, nullable=True)
    actual_time = Column(Float, nullable=True)
    plan_depth = Column(Integer, nullable=True)
    
    # Plan metadata
    plan_type = Column(String(50), nullable=True)  # e.g., "EXPLAIN", "EXPLAIN ANALYZE"
    
    def __repr__(self) -> str:
        """String representation of the execution plan."""
        return f"<ExecutionPlan(id={self.id}, query_id={self.query_id}, cost={self.total_cost})>" 