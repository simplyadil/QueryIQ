import asyncio
from datetime import datetime
from typing import List, Optional
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import asyncpg

from app.models.query_log import QueryLog
from app.core.logger import logger
from app.core.config import settings


class QueryCollector:
    """Service for collecting query statistics from pg_stat_statements."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    async def collect_queries(self, session: AsyncSession) -> List[QueryLog]:
        """
        Collect query statistics from pg_stat_statements and store them.
        
        Returns:
            List of newly created QueryLog instances
        """
        try:
            # Connect to PostgreSQL to read pg_stat_statements
            conn = await asyncpg.connect(self.db_url)
            
            # Query pg_stat_statements for slow queries
            query = """
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    stddev_exec_time,
                    min_exec_time,
                    max_exec_time
                FROM pg_stat_statements 
                WHERE mean_exec_time > $1
                ORDER BY mean_exec_time DESC
                LIMIT 100
            """
            
            rows = await conn.fetch(query, settings.slow_query_threshold_ms)
            await conn.close()
            
            # Process and store query logs
            query_logs = []
            for row in rows:
                # Create hash for query identification
                query_hash = hashlib.md5(row['query'].encode()).hexdigest()
                
                # Check if query already exists
                existing_query = await session.execute(
                    select(QueryLog).where(QueryLog.query_hash == query_hash)
                )
                existing_query = existing_query.scalar_one_or_none()
                
                if existing_query:
                    # Update existing query with new statistics
                    existing_query.calls = row['calls']
                    existing_query.total_exec_time = row['total_exec_time']
                    existing_query.mean_exec_time = row['mean_exec_time']
                    existing_query.updated_at = datetime.utcnow()
                    query_logs.append(existing_query)
                else:
                    # Create new query log
                    query_log = QueryLog(
                        query_text=row['query'],
                        query_hash=query_hash,
                        total_exec_time=row['total_exec_time'],
                        mean_exec_time=row['mean_exec_time'],
                        calls=row['calls'],
                        collected_at=datetime.utcnow()
                    )
                    session.add(query_log)
                    query_logs.append(query_log)
            
            await session.commit()
            logger.info(f"Collected {len(query_logs)} queries from pg_stat_statements")
            return query_logs
            
        except Exception as e:
            logger.error(f"Error collecting queries: {e}")
            await session.rollback()
            raise
    
    async def get_slow_queries(self, session: AsyncSession, limit: int = 10) -> List[QueryLog]:
        """
        Get the slowest queries from the database.
        
        Args:
            session: Database session
            limit: Maximum number of queries to return
            
        Returns:
            List of slowest QueryLog instances
        """
        result = await session.execute(
            select(QueryLog)
            .order_by(QueryLog.mean_exec_time.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_query_by_hash(self, session: AsyncSession, query_hash: str) -> Optional[QueryLog]:
        """
        Get a specific query by its hash.
        
        Args:
            session: Database session
            query_hash: Hash of the query
            
        Returns:
            QueryLog instance if found, None otherwise
        """
        result = await session.execute(
            select(QueryLog).where(QueryLog.query_hash == query_hash)
        )
        return result.scalar_one_or_none()
    
    async def get_queries_by_user(self, session: AsyncSession, db_user: str) -> List[QueryLog]:
        """
        Get all queries executed by a specific user.
        
        Args:
            session: Database session
            db_user: Database user name
            
        Returns:
            List of QueryLog instances for the user
        """
        result = await session.execute(
            select(QueryLog).where(QueryLog.db_user == db_user)
        )
        return result.scalars().all()


# Global instance
query_collector = QueryCollector(settings.database_url) 