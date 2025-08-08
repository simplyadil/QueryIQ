from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class QueryLog(Base):
    """Model for storing query execution logs from pg_stat_statements."""
    
    __tablename__ = "query_logs"
    
    # Query information
    query_text = Column(Text, nullable=False, index=True)
    query_hash = Column(String(64), nullable=False, index=True)
    
    # Database context
    db_user = Column(String(100), nullable=True)
    database_name = Column(String(100), nullable=True)
    
    # Performance metrics
    total_exec_time = Column(Float, nullable=False, default=0.0)
    mean_exec_time = Column(Float, nullable=False, default=0.0)
    calls = Column(Integer, nullable=False, default=0)
    
    # Collection metadata
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of the query log."""
        return f"<QueryLog(id={self.id}, hash={self.query_hash}, calls={self.calls})>" 