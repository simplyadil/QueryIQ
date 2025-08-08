from typing import Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.models.query_log import QueryLog
from app.models.suggestion import Suggestion
from app.models.features import QueryFeature
from app.core.logger import logger

router = APIRouter()


@router.get("/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    Get system overview statistics.
    
    Args:
        db: Database session
        
    Returns:
        System overview statistics
    """
    try:
        # Get total queries
        total_queries_result = await db.execute(select(func.count(QueryLog.id)))
        total_queries = total_queries_result.scalar()
        
        # Get slow queries count
        slow_queries_result = await db.execute(
            select(func.count(QueryLog.id)).where(QueryLog.mean_exec_time > 1000)
        )
        slow_queries = slow_queries_result.scalar()
        
        # Get total suggestions
        total_suggestions_result = await db.execute(select(func.count(Suggestion.id)))
        total_suggestions = total_suggestions_result.scalar()
        
        # Get average execution time
        avg_time_result = await db.execute(select(func.avg(QueryLog.mean_exec_time)))
        avg_execution_time = avg_time_result.scalar() or 0.0
        
        # Get total execution time
        total_time_result = await db.execute(select(func.sum(QueryLog.total_exec_time)))
        total_execution_time = total_time_result.scalar() or 0.0
        
        return {
            "total_queries": total_queries,
            "slow_queries": slow_queries,
            "total_suggestions": total_suggestions,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "total_execution_time_ms": round(total_execution_time, 2),
            "slow_query_percentage": round((slow_queries / total_queries * 100) if total_queries > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/performance")
async def get_performance_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance statistics.
    
    Args:
        db: Database session
        
    Returns:
        Performance statistics
    """
    try:
        # Get top 10 slowest queries
        slowest_queries_result = await db.execute(
            select(QueryLog)
            .order_by(desc(QueryLog.mean_exec_time))
            .limit(10)
        )
        slowest_queries = slowest_queries_result.scalars().all()
        
        # Get execution time distribution
        time_ranges = [
            (0, 100, "0-100ms"),
            (100, 500, "100-500ms"),
            (500, 1000, "500ms-1s"),
            (1000, 5000, "1s-5s"),
            (5000, float('inf'), "5s+")
        ]
        
        distribution = {}
        for min_time, max_time, label in time_ranges:
            if max_time == float('inf'):
                count_result = await db.execute(
                    select(func.count(QueryLog.id)).where(QueryLog.mean_exec_time >= min_time)
                )
            else:
                count_result = await db.execute(
                    select(func.count(QueryLog.id)).where(
                        QueryLog.mean_exec_time >= min_time,
                        QueryLog.mean_exec_time < max_time
                    )
                )
            distribution[label] = count_result.scalar()
        
        return {
            "slowest_queries": [
                {
                    "id": str(q.id),
                    "query_text": q.query_text[:100] + "..." if len(q.query_text) > 100 else q.query_text,
                    "mean_exec_time": q.mean_exec_time,
                    "calls": q.calls
                }
                for q in slowest_queries
            ],
            "execution_time_distribution": distribution
        }
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suggestions")
async def get_suggestion_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get suggestion statistics.
    
    Args:
        db: Database session
        
    Returns:
        Suggestion statistics
    """
    try:
        # Get suggestions by type
        suggestion_types_result = await db.execute(
            select(Suggestion.suggestion_type, func.count(Suggestion.id))
            .group_by(Suggestion.suggestion_type)
        )
        suggestion_types = dict(suggestion_types_result.all())
        
        # Get suggestions by source
        suggestion_sources_result = await db.execute(
            select(Suggestion.source, func.count(Suggestion.id))
            .group_by(Suggestion.source)
        )
        suggestion_sources = dict(suggestion_sources_result.all())
        
        # Get average confidence
        avg_confidence_result = await db.execute(select(func.avg(Suggestion.confidence)))
        avg_confidence = avg_confidence_result.scalar() or 0.0
        
        # Get high confidence suggestions (>0.8)
        high_confidence_result = await db.execute(
            select(func.count(Suggestion.id)).where(Suggestion.confidence > 0.8)
        )
        high_confidence_count = high_confidence_result.scalar()
        
        return {
            "suggestions_by_type": suggestion_types,
            "suggestions_by_source": suggestion_sources,
            "avg_confidence": round(avg_confidence, 3),
            "high_confidence_suggestions": high_confidence_count,
            "total_suggestions": sum(suggestion_types.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestion stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends")
async def get_trends(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get trends over the last N days.
    
    Args:
        days: Number of days to analyze
        db: Database session
        
    Returns:
        Trend data
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily query counts
        daily_queries_result = await db.execute(
            select(
                func.date(QueryLog.collected_at).label('date'),
                func.count(QueryLog.id).label('count')
            )
            .where(QueryLog.collected_at >= start_date)
            .group_by(func.date(QueryLog.collected_at))
            .order_by(func.date(QueryLog.collected_at))
        )
        daily_queries = daily_queries_result.all()
        
        # Get daily slow query counts
        daily_slow_queries_result = await db.execute(
            select(
                func.date(QueryLog.collected_at).label('date'),
                func.count(QueryLog.id).label('count')
            )
            .where(
                QueryLog.collected_at >= start_date,
                QueryLog.mean_exec_time > 1000
            )
            .group_by(func.date(QueryLog.collected_at))
            .order_by(func.date(QueryLog.collected_at))
        )
        daily_slow_queries = daily_slow_queries_result.all()
        
        return {
            "period_days": days,
            "daily_queries": [
                {"date": str(row.date), "count": row.count}
                for row in daily_queries
            ],
            "daily_slow_queries": [
                {"date": str(row.date), "count": row.count}
                for row in daily_slow_queries
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 