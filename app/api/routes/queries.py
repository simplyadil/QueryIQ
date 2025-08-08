from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.query_log import QueryLog
from app.schemas.query import QueryLogResponse, QueryLogList, SlowQueryResponse
from app.services.query_collector import query_collector
from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=QueryLogList)
async def list_queries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all query logs with pagination.
    
    Args:
        page: Page number (1-based)
        size: Number of items per page
        db: Database session
        
    Returns:
        Paginated list of query logs
    """
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Get total count
        count_result = await db.execute(select(QueryLog))
        total = len(count_result.scalars().all())
        
        # Get paginated results
        result = await db.execute(
            select(QueryLog)
            .order_by(QueryLog.collected_at.desc())
            .offset(offset)
            .limit(size)
        )
        
        queries = result.scalars().all()
        
        return QueryLogList(
            queries=[QueryLogResponse.model_validate(query) for query in queries],
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"Error listing queries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/slow", response_model=List[SlowQueryResponse])
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=100, description="Number of slow queries to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the slowest queries from the database.
    
    Args:
        limit: Maximum number of queries to return
        db: Database session
        
    Returns:
        List of slowest queries
    """
    try:
        slow_queries = await query_collector.get_slow_queries(db, limit)
        
        return [
            SlowQueryResponse(
                id=query.id,
                query_text=query.query_text,
                query_hash=query.query_hash,
                mean_exec_time=query.mean_exec_time,
                calls=query.calls,
                total_exec_time=query.total_exec_time,
                collected_at=query.collected_at,
                is_slow=query.mean_exec_time > 1000  # 1 second threshold
            )
            for query in slow_queries
        ]
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{query_id}", response_model=QueryLogResponse)
async def get_query(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific query by ID.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Query log details
    """
    try:
        result = await db.execute(select(QueryLog).where(QueryLog.id == query_id))
        query = result.scalar_one_or_none()
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        return QueryLogResponse.model_validate(query)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/collect")
async def collect_queries(
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger query collection from pg_stat_statements.
    
    Args:
        db: Database session
        
    Returns:
        Collection results
    """
    try:
        collected_queries = await query_collector.collect_queries(db)
        
        return {
            "message": f"Successfully collected {len(collected_queries)} queries",
            "collected_count": len(collected_queries)
        }
        
    except Exception as e:
        logger.error(f"Error collecting queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect queries")


@router.get("/hash/{query_hash}", response_model=QueryLogResponse)
async def get_query_by_hash(
    query_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific query by its hash.
    
    Args:
        query_hash: Query hash
        db: Database session
        
    Returns:
        Query log details
    """
    try:
        query = await query_collector.get_query_by_hash(db, query_hash)
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        return QueryLogResponse.model_validate(query)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting query by hash {query_hash}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 