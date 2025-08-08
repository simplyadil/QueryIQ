import asyncio
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.query_log import QueryLog
from app.models.execution_plan import ExecutionPlan
from app.models.features import QueryFeature
from app.models.suggestion import Suggestion
from app.core.logger import logger


async def create_sample_data() -> None:
    """Create sample data for development and testing."""
    async with AsyncSessionLocal() as session:
        # Create sample query logs
        sample_queries = [
            {
                "query_text": "SELECT * FROM users WHERE email = 'test@example.com'",
                "query_hash": "abc123",
                "db_user": "postgres",
                "database_name": "testdb",
                "total_exec_time": 150.5,
                "mean_exec_time": 75.2,
                "calls": 10,
                "collected_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "query_text": "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id WHERE u.active = true",
                "query_hash": "def456",
                "db_user": "postgres",
                "database_name": "testdb",
                "total_exec_time": 2500.0,
                "mean_exec_time": 500.0,
                "calls": 5,
                "collected_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "query_text": "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'",
                "query_hash": "ghi789",
                "db_user": "postgres",
                "database_name": "testdb",
                "total_exec_time": 800.0,
                "mean_exec_time": 200.0,
                "calls": 4,
                "collected_at": datetime.utcnow() - timedelta(hours=3)
            }
        ]
        
        query_logs = []
        for query_data in sample_queries:
            query_log = QueryLog(**query_data)
            session.add(query_log)
            query_logs.append(query_log)
        
        await session.commit()
        
        # Create sample execution plans
        for query_log in query_logs:
            plan = ExecutionPlan(
                query_id=query_log.id,
                plan_json={
                    "Node Type": "Seq Scan",
                    "Total Cost": 100.0,
                    "Actual Time": query_log.mean_exec_time,
                    "Plan Rows": 1000,
                    "Actual Rows": 1000
                },
                total_cost=100.0,
                actual_time=query_log.mean_exec_time,
                plan_depth=1,
                plan_type="EXPLAIN ANALYZE"
            )
            session.add(plan)
        
        await session.commit()
        
        # Create sample features
        for query_log in query_logs:
            feature = QueryFeature(
                query_id=query_log.id,
                num_joins=1 if "JOIN" in query_log.query_text else 0,
                has_select_star="SELECT *" in query_log.query_text,
                has_where_clause="WHERE" in query_log.query_text,
                num_subqueries=0,
                scan_types=["Seq Scan"],
                indexed_tables_pct=50.0,
                avg_table_size_mb=10.0,
                is_slow_query=query_log.mean_exec_time > 100,
                complexity_score=0.5
            )
            session.add(feature)
        
        await session.commit()
        
        # Create sample suggestions
        for query_log in query_logs:
            if "SELECT *" in query_log.query_text:
                suggestion = Suggestion(
                    query_id=query_log.id,
                    suggestion_type="QUERY_REWRITE",
                    message="Consider replacing SELECT * with specific column names to improve performance",
                    confidence=0.8,
                    source="RULE_ENGINE",
                    estimated_improvement_ms=50.0,
                    implementation_cost="LOW"
                )
                session.add(suggestion)
            
            if query_log.mean_exec_time > 100:
                suggestion = Suggestion(
                    query_id=query_log.id,
                    suggestion_type="INDEX",
                    message="Consider adding an index on frequently queried columns",
                    confidence=0.7,
                    source="HEURISTIC",
                    estimated_improvement_ms=200.0,
                    implementation_cost="MEDIUM"
                )
                session.add(suggestion)
        
        await session.commit()
        
        logger.info("Sample data created successfully")


async def init_database() -> None:
    """Initialize the database with tables and sample data."""
    from app.db.session import init_db
    
    try:
        await init_db()
        logger.info("Database tables created successfully")
        
        # Create sample data for development
        await create_sample_data()
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database()) 