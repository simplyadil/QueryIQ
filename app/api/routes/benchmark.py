# app/api/routes/benchmark.py
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.query_log import QueryLog
from app.models.suggestion import Suggestion
from app.services.benchmark_engine import benchmark_engine, BenchmarkResult
from app.services.rule_engine import rule_engine
from app.core.logger import logger

router = APIRouter()


@router.post("/run/{query_id}")
async def run_benchmark(
    query_id: UUID,
    background_tasks: BackgroundTasks,
    iterations: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    Run a comprehensive benchmark for a specific query.
    
    Args:
        query_id: Query ID to benchmark
        background_tasks: FastAPI background tasks
        iterations: Number of benchmark iterations
        db: Database session
        
    Returns:
        Benchmark initiation confirmation
    """
    try:
        # Get the query
        result = await db.execute(select(QueryLog).where(QueryLog.id == query_id))
        query_log = result.scalar_one_or_none()
        
        if not query_log:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get suggestions for the query
        suggestions = await rule_engine.get_suggestions_for_query(db, str(query_id))
        
        if not suggestions:
            # Generate suggestions if none exist
            suggestions = await rule_engine.generate_suggestions(db, query_log)
        
        # Run benchmark in background
        background_tasks.add_task(
            run_benchmark_task, 
            query_log, 
            suggestions, 
            iterations
        )
        
        return {
            "message": f"Benchmark started for query {query_id}",
            "query_id": str(query_id),
            "iterations": iterations,
            "suggestions_count": len(suggestions),
            "status": "running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting benchmark for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start benchmark")


async def run_benchmark_task(
    query_log: QueryLog,
    suggestions: List[Suggestion], 
    iterations: int
):
    """Background task to run the actual benchmark."""
    try:
        from app.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            result = await benchmark_engine.run_comprehensive_benchmark(
                session, query_log, suggestions, iterations
            )
            
            logger.info(f"Background benchmark completed for query {query_log.id}: "
                       f"{result.improvement_pct:.1f}% improvement")
            
    except Exception as e:
        logger.error(f"Background benchmark failed for query {query_log.id}: {e}")


@router.get("/results/{query_id}")
async def get_benchmark_results(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get benchmark results for a specific query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Benchmark results for the query
    """
    try:
        from sqlalchemy import text
        
        results_query = text("""
            SELECT * FROM performance_improvements 
            WHERE query_id = :query_id 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        result = await db.execute(results_query, {"query_id": str(query_id)})
        results = result.fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="No benchmark results found for this query")
        
        return {
            "query_id": str(query_id),
            "results": [
                {
                    "id": str(row[0]),
                    "original_avg_ms": row[4],
                    "optimized_avg_ms": row[5], 
                    "improvement_pct": row[6],
                    "improvement_ms": row[7],
                    "confidence": row[8],
                    "optimization_type": row[9],
                    "success": row[10],
                    "created_at": row[12].isoformat() if row[12] else None
                }
                for row in results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting benchmark results for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get benchmark results")


@router.get("/summary")
async def get_benchmark_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall benchmark summary statistics.
    
    Args:
        db: Database session
        
    Returns:
        Summary statistics of all benchmarks
    """
    try:
        summary = await benchmark_engine.get_benchmark_summary(db)
        
        return {
            "summary": summary,
            "generated_at": "2024-01-01T00:00:00Z"  # Use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error getting benchmark summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get benchmark summary")


@router.get("/top-improvements")
async def get_top_improvements(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the queries with the highest performance improvements.
    
    Args:
        limit: Number of top improvements to return
        db: Database session
        
    Returns:
        List of top performing optimizations
    """
    try:
        from sqlalchemy import text
        
        top_query = text("""
            SELECT 
                pi.query_id,
                pi.original_query,
                pi.optimized_query,
                pi.improvement_pct,
                pi.improvement_ms,
                pi.confidence,
                pi.optimization_type,
                pi.created_at
            FROM performance_improvements pi
            WHERE pi.success = true 
            ORDER BY pi.improvement_pct DESC 
            LIMIT :limit
        """)
        
        result = await db.execute(top_query, {"limit": limit})
        improvements = result.fetchall()
        
        return {
            "top_improvements": [
                {
                    "query_id": str(row[0]),
                    "original_query": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                    "optimized_query": row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                    "improvement_pct": row[3],
                    "improvement_ms": row[4],
                    "confidence": row[5],
                    "optimization_type": row[6],
                    "created_at": row[7].isoformat() if row[7] else None
                }
                for row in improvements
            ],
            "count": len(improvements)
        }
        
    except Exception as e:
        logger.error(f"Error getting top improvements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get top improvements")


@router.post("/batch-benchmark")
async def run_batch_benchmark(
    background_tasks: BackgroundTasks,
    limit: int = 50,
    min_execution_time: float = 100.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Run benchmarks on multiple slow queries in batch.
    
    Args:
        background_tasks: FastAPI background tasks
        limit: Maximum number of queries to benchmark
        min_execution_time: Minimum execution time to consider for benchmarking
        db: Database session
        
    Returns:
        Batch benchmark initiation confirmation
    """
    try:
        # Get slow queries that haven't been benchmarked recently
        from sqlalchemy import text
        
        slow_queries_query = text("""
            SELECT ql.* FROM query_logs ql
            LEFT JOIN performance_improvements pi ON ql.id::text = pi.query_id
            WHERE ql.mean_exec_time > :min_time
            AND (pi.created_at IS NULL OR pi.created_at < NOW() - INTERVAL '24 hours')
            ORDER BY ql.mean_exec_time DESC
            LIMIT :limit
        """)
        
        result = await db.execute(slow_queries_query, {
            "min_time": min_execution_time,
            "limit": limit
        })
        
        queries = result.fetchall()
        
        if not queries:
            return {
                "message": "No queries found for batch benchmarking",
                "queries_count": 0
            }
        
        # Start batch benchmark in background
        background_tasks.add_task(run_batch_benchmark_task, [dict(q._mapping) for q in queries])
        
        return {
            "message": f"Batch benchmark started for {len(queries)} queries",
            "queries_count": len(queries),
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error starting batch benchmark: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch benchmark")


async def run_batch_benchmark_task(queries_data: List[Dict[str, Any]]):
    """Background task to run batch benchmarks."""
    try:
        from app.db.session import AsyncSessionLocal
        
        logger.info(f"Starting batch benchmark for {len(queries_data)} queries")
        
        successful = 0
        failed = 0
        
        for query_data in queries_data:
            try:
                async with AsyncSessionLocal() as session:
                    # Reconstruct QueryLog object
                    query_log = QueryLog(**query_data)
                    
                    # Get or generate suggestions
                    suggestions = await rule_engine.get_suggestions_for_query(
                        session, str(query_log.id)
                    )
                    
                    if not suggestions:
                        suggestions = await rule_engine.generate_suggestions(session, query_log)
                    
                    # Run benchmark
                    result = await benchmark_engine.run_comprehensive_benchmark(
                        session, query_log, suggestions, iterations=3
                    )
                    
                    if result.success:
                        successful += 1
                        logger.info(f"Batch benchmark success for query {query_log.id}: "
                                   f"{result.improvement_pct:.1f}% improvement")
                    else:
                        failed += 1
                        logger.warning(f"Batch benchmark failed for query {query_log.id}")
                        
            except Exception as e:
                failed += 1
                logger.error(f"Error in batch benchmark for query: {e}")
        
        logger.info(f"Batch benchmark completed: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Batch benchmark task failed: {e}")