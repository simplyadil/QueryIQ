from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.suggestion import Suggestion
from app.models.query_log import QueryLog
from app.models.features import QueryFeature
from app.models.execution_plan import ExecutionPlan
from app.core.logger import logger
from app.core.config import settings


class RuleEngine:
    """Service for applying heuristics and rules to generate optimization suggestions."""
    
    async def generate_suggestions(
        self, 
        session: AsyncSession, 
        query_log: QueryLog, 
        query_feature: Optional[QueryFeature] = None,
        execution_plan: Optional[ExecutionPlan] = None
    ) -> List[Suggestion]:
        """
        Generate optimization suggestions based on query analysis.
        
        Args:
            session: Database session
            query_log: QueryLog instance
            query_feature: Optional QueryFeature instance
            execution_plan: Optional ExecutionPlan instance
            
        Returns:
            List of Suggestion instances
        """
        suggestions = []
        
        # Apply various rule sets
        suggestions.extend(await self._apply_query_structure_rules(query_log, query_feature))
        suggestions.extend(await self._apply_performance_rules(query_log, query_feature))
        suggestions.extend(await self._apply_plan_based_rules(query_log, execution_plan))
        suggestions.extend(await self._apply_index_rules(query_log, query_feature, execution_plan))
        
        # Limit suggestions to configured maximum
        if len(suggestions) > settings.max_suggestions_per_query:
            suggestions = suggestions[:settings.max_suggestions_per_query]
        
        # Save suggestions to database
        for suggestion in suggestions:
            suggestion.query_id = query_log.id
            session.add(suggestion)
        
        await session.commit()
        
        logger.info(f"Generated {len(suggestions)} suggestions for query {query_log.id}")
        return suggestions
    
    async def _apply_query_structure_rules(
        self, 
        query_log: QueryLog, 
        query_feature: Optional[QueryFeature]
    ) -> List[Suggestion]:
        """Apply rules based on query structure analysis."""
        suggestions = []
        
        if not query_feature:
            return suggestions
        
        # Rule: SELECT * optimization
        if query_feature.has_select_star:
            suggestions.append(Suggestion(
                suggestion_type="QUERY_REWRITE",
                message="Consider replacing SELECT * with specific column names to improve performance and reduce network transfer",
                confidence=0.8,
                source="RULE_ENGINE",
                estimated_improvement_ms=50.0,
                implementation_cost="LOW"
            ))
        
        # Rule: Missing WHERE clause
        if not query_feature.has_where_clause and "SELECT" in query_log.query_text.upper():
            suggestions.append(Suggestion(
                suggestion_type="QUERY_REWRITE",
                message="Consider adding a WHERE clause to filter results and improve performance",
                confidence=0.6,
                source="RULE_ENGINE",
                estimated_improvement_ms=100.0,
                implementation_cost="LOW"
            ))
        
        # Rule: Complex queries with many joins
        if query_feature.num_joins > 3:
            suggestions.append(Suggestion(
                suggestion_type="QUERY_REWRITE",
                message=f"Query has {query_feature.num_joins} joins. Consider breaking it into smaller queries or adding indexes",
                confidence=0.7,
                source="RULE_ENGINE",
                estimated_improvement_ms=200.0,
                implementation_cost="MEDIUM"
            ))
        
        # Rule: Subqueries
        if query_feature.num_subqueries > 0:
            suggestions.append(Suggestion(
                suggestion_type="QUERY_REWRITE",
                message="Consider replacing subqueries with JOINs for better performance",
                confidence=0.6,
                source="RULE_ENGINE",
                estimated_improvement_ms=150.0,
                implementation_cost="MEDIUM"
            ))
        
        return suggestions
    
    async def _apply_performance_rules(
        self, 
        query_log: QueryLog, 
        query_feature: Optional[QueryFeature]
    ) -> List[Suggestion]:
        """Apply rules based on performance metrics."""
        suggestions = []
        
        # Rule: Slow query threshold
        if query_log.mean_exec_time > settings.slow_query_threshold_ms:
            suggestions.append(Suggestion(
                suggestion_type="PERFORMANCE",
                message=f"Query execution time ({query_log.mean_exec_time:.2f}ms) exceeds threshold. Consider optimization",
                confidence=0.9,
                source="RULE_ENGINE",
                estimated_improvement_ms=query_log.mean_exec_time * 0.5,
                implementation_cost="HIGH"
            ))
        
        # Rule: High call frequency
        if query_log.calls > 1000:
            suggestions.append(Suggestion(
                suggestion_type="CACHING",
                message=f"Query called {query_log.calls} times. Consider implementing caching or query optimization",
                confidence=0.8,
                source="RULE_ENGINE",
                estimated_improvement_ms=100.0,
                implementation_cost="MEDIUM"
            ))
        
        # Rule: High total execution time
        if query_log.total_exec_time > 10000:  # 10 seconds total
            suggestions.append(Suggestion(
                suggestion_type="PERFORMANCE",
                message=f"Total execution time is {query_log.total_exec_time:.2f}ms. This query needs optimization",
                confidence=0.9,
                source="RULE_ENGINE",
                estimated_improvement_ms=query_log.total_exec_time * 0.3,
                implementation_cost="HIGH"
            ))
        
        return suggestions
    
    async def _apply_plan_based_rules(
        self, 
        query_log: QueryLog, 
        execution_plan: Optional[ExecutionPlan]
    ) -> List[Suggestion]:
        """Apply rules based on execution plan analysis."""
        suggestions = []
        
        if not execution_plan:
            return suggestions
        
        # Rule: Sequential scans
        if execution_plan.plan_json and "Seq Scan" in str(execution_plan.plan_json):
            suggestions.append(Suggestion(
                suggestion_type="INDEX",
                message="Query uses sequential scan. Consider adding indexes on frequently queried columns",
                confidence=0.8,
                source="RULE_ENGINE",
                estimated_improvement_ms=300.0,
                implementation_cost="MEDIUM"
            ))
        
        # Rule: High cost plans
        if execution_plan.total_cost and execution_plan.total_cost > 1000:
            suggestions.append(Suggestion(
                suggestion_type="OPTIMIZATION",
                message=f"Execution plan has high cost ({execution_plan.total_cost:.2f}). Consider query rewrite or indexing",
                confidence=0.7,
                source="RULE_ENGINE",
                estimated_improvement_ms=200.0,
                implementation_cost="HIGH"
            ))
        
        # Rule: Deep plan trees
        if execution_plan.plan_depth and execution_plan.plan_depth > 5:
            suggestions.append(Suggestion(
                suggestion_type="QUERY_REWRITE",
                message=f"Execution plan is deep ({execution_plan.plan_depth} levels). Consider simplifying the query",
                confidence=0.6,
                source="RULE_ENGINE",
                estimated_improvement_ms=150.0,
                implementation_cost="MEDIUM"
            ))
        
        return suggestions
    
    async def _apply_index_rules(
        self, 
        query_log: QueryLog, 
        query_feature: Optional[QueryFeature],
        execution_plan: Optional[ExecutionPlan]
    ) -> List[Suggestion]:
        """Apply rules related to indexing."""
        suggestions = []
        
        # Rule: Low indexed tables percentage
        if query_feature and query_feature.indexed_tables_pct and query_feature.indexed_tables_pct < 50:
            suggestions.append(Suggestion(
                suggestion_type="INDEX",
                message=f"Only {query_feature.indexed_tables_pct:.1f}% of tables have indexes. Consider adding indexes",
                confidence=0.7,
                source="RULE_ENGINE",
                estimated_improvement_ms=250.0,
                implementation_cost="MEDIUM"
            ))
        
        # Rule: WHERE clause without indexes
        if query_feature and query_feature.has_where_clause:
            # This is a simplified check - in reality you'd analyze the WHERE clause
            suggestions.append(Suggestion(
                suggestion_type="INDEX",
                message="Query has WHERE clause. Ensure indexed columns are used in WHERE conditions",
                confidence=0.6,
                source="RULE_ENGINE",
                estimated_improvement_ms=100.0,
                implementation_cost="LOW"
            ))
        
        return suggestions
    
    async def get_suggestions_for_query(
        self, 
        session: AsyncSession, 
        query_id: str
    ) -> List[Suggestion]:
        """
        Get all suggestions for a specific query.
        
        Args:
            session: Database session
            query_id: Query ID
            
        Returns:
            List of Suggestion instances
        """
        from sqlalchemy import select
        
        result = await session.execute(
            select(Suggestion).where(Suggestion.query_id == query_id)
        )
        return result.scalars().all()


# Global instance
rule_engine = RuleEngine() 