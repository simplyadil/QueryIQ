import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import asyncpg

from app.models.query_log import QueryLog
from app.models.suggestion import Suggestion
from app.services.gemini_optimizer import gemini_optimizer, OptimizationResult
from app.core.logger import logger
from app.core.config import settings


@dataclass
class BenchmarkResult:
    """Result of a query benchmark test."""
    query_id: str
    original_query: str
    optimized_query: str
    original_times: List[float]
    optimized_times: List[float]
    original_avg_ms: float
    optimized_avg_ms: float
    improvement_pct: float
    improvement_ms: float
    success: bool
    error_message: Optional[str] = None
    confidence: float = 0.0
    optimization_type: str = "UNKNOWN"


class BenchmarkEngine:
    """Engine for benchmarking query optimizations and measuring real improvements."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    async def run_comprehensive_benchmark(
        self, 
        session: AsyncSession,
        query_log: QueryLog,
        suggestions: List[Suggestion],
        iterations: int = 5
    ) -> BenchmarkResult:
        """
        Run a complete benchmark: optimize query with Gemini, then measure performance.
        
        Args:
            session: Database session
            query_log: Original query log
            suggestions: Optimization suggestions
            iterations: Number of test runs for averaging
            
        Returns:
            BenchmarkResult with performance comparison
        """
        logger.info(f"Starting benchmark for query {query_log.id}")
        
        try:
            # Step 1: Get table schemas for context
            table_schemas = await self._extract_table_schemas(session, query_log.query_text)
            
            # Step 2: Use Gemini to optimize the query
            optimization_result = await gemini_optimizer.optimize_query(
                query_log.query_text, 
                suggestions, 
                table_schemas
            )
            
            # Step 3: Benchmark both queries
            original_times = await self._benchmark_query(
                query_log.query_text, 
                iterations
            )
            
            optimized_times = await self._benchmark_query(
                optimization_result.optimized_query, 
                iterations
            )
            
            # Step 4: Calculate improvement metrics
            original_avg = statistics.mean(original_times)
            optimized_avg = statistics.mean(optimized_times)
            improvement_ms = original_avg - optimized_avg
            improvement_pct = (improvement_ms / original_avg) * 100 if original_avg > 0 else 0
            
            result = BenchmarkResult(
                query_id=str(query_log.id),
                original_query=query_log.query_text,
                optimized_query=optimization_result.optimized_query,
                original_times=original_times,
                optimized_times=optimized_times,
                original_avg_ms=original_avg,
                optimized_avg_ms=optimized_avg,
                improvement_pct=improvement_pct,
                improvement_ms=improvement_ms,
                success=True,
                confidence=optimization_result.confidence,
                optimization_type=optimization_result.optimization_type
            )
            
            # Step 5: Store results
            await self._store_benchmark_result(session, result)
            
            logger.info(f"Benchmark completed: {improvement_pct:.1f}% improvement ({improvement_ms:.1f}ms)")
            return result
            
        except Exception as e:
            logger.error(f"Benchmark failed for query {query_log.id}: {e}")
            return BenchmarkResult(
                query_id=str(query_log.id),
                original_query=query_log.query_text,
                optimized_query=query_log.query_text,
                original_times=[0.0],
                optimized_times=[0.0],
                original_avg_ms=0.0,
                optimized_avg_ms=0.0,
                improvement_pct=0.0,
                improvement_ms=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def _benchmark_query(self, query: str, iterations: int = 5) -> List[float]:
        """
        Execute a query multiple times and measure execution times.
        
        Args:
            query: SQL query to benchmark
            iterations: Number of times to run the query
            
        Returns:
            List of execution times in milliseconds
        """
        times = []
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Warm up the connection
            await conn.execute("SELECT 1")
            
            for i in range(iterations):
                start_time = time.perf_counter()
                
                try:
                    # Execute query and fetch results to ensure full execution
                    result = await conn.fetch(query)
                    
                    end_time = time.perf_counter()
                    execution_time_ms = (end_time - start_time) * 1000
                    times.append(execution_time_ms)
                    
                    # Small delay between iterations
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Query execution failed on iteration {i+1}: {e}")
                    # Use a high time to indicate failure
                    times.append(10000.0)
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Benchmark connection failed: {e}")
            times = [10000.0] * iterations  # Fallback times
        
        return times
    
    async def _extract_table_schemas(
        self, 
        session: AsyncSession, 
        query: str
    ) -> Dict[str, List[str]]:
        """Extract table schemas for tables used in the query."""
        schemas = {}
        
        try:
            # Simple regex to find table names (this could be improved with SQL parsing)
            import re
            table_pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b'
            tables = set(re.findall(table_pattern, query, re.IGNORECASE))
            
            for table in tables:
                # Get column names from information_schema
                column_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                result = await session.execute(column_query, {"table_name": table})
                columns = [row[0] for row in result.fetchall()]
                
                if columns:
                    schemas[table] = columns
                    
        except Exception as e:
            logger.warning(f"Failed to extract table schemas: {e}")
        
        return schemas
    
    async def _store_benchmark_result(
        self, 
        session: AsyncSession, 
        result: BenchmarkResult
    ):
        """Store benchmark results in the database."""
        try:
            # Create the performance_improvements table if it doesn't exist
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS performance_improvements (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    query_id UUID,
                    original_query TEXT,
                    optimized_query TEXT,
                    original_avg_ms FLOAT,
                    optimized_avg_ms FLOAT,
                    improvement_pct FLOAT,
                    improvement_ms FLOAT,
                    confidence FLOAT,
                    optimization_type VARCHAR(100),
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert the benchmark result
            insert_query = text("""
                INSERT INTO performance_improvements (
                    query_id, original_query, optimized_query, original_avg_ms,
                    optimized_avg_ms, improvement_pct, improvement_ms, confidence,
                    optimization_type, success, error_message
                ) VALUES (
                    :query_id, :original_query, :optimized_query, :original_avg_ms,
                    :optimized_avg_ms, :improvement_pct, :improvement_ms, :confidence,
                    :optimization_type, :success, :error_message
                )
            """)
            
            await session.execute(insert_query, {
                "query_id": result.query_id,
                "original_query": result.original_query,
                "optimized_query": result.optimized_query,
                "original_avg_ms": result.original_avg_ms,
                "optimized_avg_ms": result.optimized_avg_ms,
                "improvement_pct": result.improvement_pct,
                "improvement_ms": result.improvement_ms,
                "confidence": result.confidence,
                "optimization_type": result.optimization_type,
                "success": result.success,
                "error_message": result.error_message
            })
            
            await session.commit()
            logger.info(f"Stored benchmark result for query {result.query_id}")
            
        except Exception as e:
            logger.error(f"Failed to store benchmark result: {e}")
            await session.rollback()
    
    async def get_benchmark_summary(self, session: AsyncSession) -> Dict[str, Any]:
        """Get summary statistics of all benchmark results."""
        try:
            summary_query = text("""
                SELECT 
                    COUNT(*) as total_benchmarks,
                    COUNT(*) FILTER (WHERE success = true) as successful_benchmarks,
                    AVG(improvement_pct) FILTER (WHERE success = true) as avg_improvement_pct,
                    SUM(improvement_ms) FILTER (WHERE success = true) as total_time_saved_ms,
                    MAX(improvement_pct) FILTER (WHERE success = true) as max_improvement_pct,
                    AVG(confidence) FILTER (WHERE success = true) as avg_confidence
                FROM performance_improvements
            """)
            
            result = await session.execute(summary_query)
            row = result.fetchone()
            
            if row:
                return {
                    "total_benchmarks": row[0] or 0,
                    "successful_benchmarks": row[1] or 0,
                    "avg_improvement_pct": round(row[2] or 0, 2),
                    "total_time_saved_ms": round(row[3] or 0, 2),
                    "total_time_saved_seconds": round((row[3] or 0) / 1000, 2),
                    "max_improvement_pct": round(row[4] or 0, 2),
                    "avg_confidence": round(row[5] or 0, 3),
                    "success_rate_pct": round(((row[1] or 0) / max(row[0], 1)) * 100, 2)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get benchmark summary: {e}")
            return {}


# Global instance
benchmark_engine = BenchmarkEngine(settings.database_url)