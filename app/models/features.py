from typing import Optional

from sqlalchemy import Column, Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.models.base import Base


class QueryFeature(Base):
    """Model for storing extracted features from queries and execution plans."""
    
    __tablename__ = "query_features"
    
    # Foreign key to query log
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Query structure features
    num_joins = Column(Integer, nullable=False, default=0)
    has_select_star = Column(Boolean, nullable=False, default=False)
    has_where_clause = Column(Boolean, nullable=False, default=False)
    num_subqueries = Column(Integer, nullable=False, default=0)
    
    # Execution plan features
    scan_types = Column(ARRAY(String), nullable=True)  # e.g., ["Seq Scan", "Index Scan"]
    indexed_tables_pct = Column(Float, nullable=True)  # Percentage of tables with indexes
    avg_table_size_mb = Column(Float, nullable=True)
    
    # Performance indicators
    is_slow_query = Column(Boolean, nullable=False, default=False)
    complexity_score = Column(Float, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the query feature."""
        return f"<QueryFeature(id={self.id}, query_id={self.query_id}, joins={self.num_joins})>" 