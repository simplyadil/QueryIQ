from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Suggestion(Base):
    """Model for storing query optimization suggestions."""
    
    __tablename__ = "suggestions"
    
    # Foreign key to query log
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Suggestion details
    suggestion_type = Column(String(100), nullable=False)  # e.g., "INDEX", "QUERY_REWRITE", "CONFIGURATION"
    message = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    
    # Source of suggestion
    source = Column(String(50), nullable=False)  # e.g., "RULE_ENGINE", "ML_MODEL", "HEURISTIC"
    
    # Additional metadata
    estimated_improvement_ms = Column(Float, nullable=True)  # Estimated time improvement
    implementation_cost = Column(String(20), nullable=True)  # e.g., "LOW", "MEDIUM", "HIGH"
    
    def __repr__(self) -> str:
        """String representation of the suggestion."""
        return f"<Suggestion(id={self.id}, type={self.suggestion_type}, confidence={self.confidence})>" 