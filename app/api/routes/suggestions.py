from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.query_log import QueryLog
from app.models.features import QueryFeature
from app.models.execution_plan import ExecutionPlan
from app.models.suggestion import Suggestion
from app.schemas.suggestion import SuggestionResponse, SuggestionList
from app.services.rule_engine import rule_engine
from app.services.feature_extractor import feature_extractor
from app.core.logger import logger

router = APIRouter()


@router.get("/{query_id}", response_model=SuggestionList)
async def get_suggestions(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get optimization suggestions for a specific query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        List of suggestions for the query
    """
    try:
        # Get the query
        result = await db.execute(select(QueryLog).where(QueryLog.id == query_id))
        query_log = result.scalar_one_or_none()
        
        if not query_log:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get existing suggestions
        suggestions = await rule_engine.get_suggestions_for_query(db, str(query_id))
        
        # If no suggestions exist, generate them
        if not suggestions:
            # Get query features
            feature_result = await db.execute(
                select(QueryFeature).where(QueryFeature.query_id == query_id)
            )
            query_feature = feature_result.scalar_one_or_none()
            
            # Get execution plan
            plan_result = await db.execute(
                select(ExecutionPlan).where(ExecutionPlan.query_id == query_id)
            )
            execution_plan = plan_result.scalar_one_or_none()
            
            # Generate new suggestions
            suggestions = await rule_engine.generate_suggestions(
                db, query_log, query_feature, execution_plan
            )
        
        return SuggestionList(
            suggestions=[SuggestionResponse.model_validate(s) for s in suggestions],
            query_id=query_id,
            total=len(suggestions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{query_id}/generate")
async def generate_suggestions(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually generate new suggestions for a query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Generation results
    """
    try:
        # Get the query
        result = await db.execute(select(QueryLog).where(QueryLog.id == query_id))
        query_log = result.scalar_one_or_none()
        
        if not query_log:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get query features
        feature_result = await db.execute(
            select(QueryFeature).where(QueryFeature.query_id == query_id)
        )
        query_feature = feature_result.scalar_one_or_none()
        
        # Get execution plan
        plan_result = await db.execute(
            select(ExecutionPlan).where(ExecutionPlan.query_id == query_id)
        )
        execution_plan = plan_result.scalar_one_or_none()
        
        # Generate suggestions
        suggestions = await rule_engine.generate_suggestions(
            db, query_log, query_feature, execution_plan
        )
        
        return {
            "message": f"Generated {len(suggestions)} suggestions for query {query_id}",
            "suggestions_count": len(suggestions),
            "query_id": str(query_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")


@router.get("/{query_id}/count")
async def get_suggestion_count(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the count of suggestions for a query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Suggestion count
    """
    try:
        suggestions = await rule_engine.get_suggestions_for_query(db, str(query_id))
        
        return {
            "query_id": str(query_id),
            "suggestion_count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestion count for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{query_id}")
async def delete_suggestions(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all suggestions for a query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Deletion results
    """
    try:
        # Get existing suggestions
        suggestions = await rule_engine.get_suggestions_for_query(db, str(query_id))
        
        # Delete them
        for suggestion in suggestions:
            await db.delete(suggestion)
        
        await db.commit()
        
        return {
            "message": f"Deleted {len(suggestions)} suggestions for query {query_id}",
            "deleted_count": len(suggestions),
            "query_id": str(query_id)
        }
        
    except Exception as e:
        logger.error(f"Error deleting suggestions for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete suggestions") 