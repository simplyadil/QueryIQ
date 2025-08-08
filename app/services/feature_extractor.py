import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.features import QueryFeature
from app.models.query_log import QueryLog
from app.models.execution_plan import ExecutionPlan
from app.services.plan_parser import plan_parser
from app.core.logger import logger
from app.core.config import settings


class FeatureExtractor:
    """Service for extracting features from SQL queries and execution plans."""
    
    def extract_query_features(self, query_text: str) -> Dict[str, Any]:
        """
        Extract features from SQL query text.
        
        Args:
            query_text: SQL query string
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            "num_joins": self._count_joins(query_text),
            "has_select_star": self._has_select_star(query_text),
            "has_where_clause": self._has_where_clause(query_text),
            "num_subqueries": self._count_subqueries(query_text),
            "query_length": len(query_text),
            "num_tables": self._count_tables(query_text),
            "has_order_by": "ORDER BY" in query_text.upper(),
            "has_group_by": "GROUP BY" in query_text.upper(),
            "has_having": "HAVING" in query_text.upper(),
            "has_limit": "LIMIT" in query_text.upper(),
            "has_distinct": "DISTINCT" in query_text.upper(),
            "has_aggregate": self._has_aggregate_functions(query_text),
            "complexity_score": self._calculate_complexity_score(query_text)
        }
        
        return features
    
    def extract_plan_features(self, plan_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from execution plan analysis.
        
        Args:
            plan_analysis: Analysis results from PlanParser
            
        Returns:
            Dictionary of extracted plan features
        """
        features = {
            "total_cost": plan_analysis.get("total_cost", 0.0),
            "actual_time": plan_analysis.get("actual_time", 0.0),
            "plan_depth": plan_analysis.get("plan_depth", 0),
            "scan_types": plan_analysis.get("scan_types", []),
            "join_types": plan_analysis.get("join_types", []),
            "has_sequential_scan": plan_analysis.get("has_sequential_scan", False),
            "has_index_scan": plan_analysis.get("has_index_scan", False),
            "estimated_rows": plan_analysis.get("estimated_rows", 0),
            "actual_rows": plan_analysis.get("actual_rows", 0),
            "tables_scanned": plan_analysis.get("tables_scanned", []),
            "indexes_used": plan_analysis.get("indexes_used", []),
            "num_sequential_scans": len([s for s in plan_analysis.get("scan_types", []) if "Seq Scan" in s]),
            "num_index_scans": len([s for s in plan_analysis.get("scan_types", []) if "Index Scan" in s])
        }
        
        return features
    
    async def create_query_features(
        self, 
        session: AsyncSession, 
        query_log: QueryLog, 
        execution_plan: Optional[ExecutionPlan] = None
    ) -> QueryFeature:
        """
        Create QueryFeature instance from query and plan data.
        
        Args:
            session: Database session
            query_log: QueryLog instance
            execution_plan: Optional ExecutionPlan instance
            
        Returns:
            QueryFeature instance
        """
        # Extract query features
        query_features = self.extract_query_features(query_log.query_text)
        
        # Extract plan features if available
        plan_features = {}
        if execution_plan:
            plan_node = plan_parser.parse_plan_json(execution_plan.plan_json)
            plan_analysis = plan_parser.analyze_plan(plan_node)
            plan_features = self.extract_plan_features(plan_analysis)
        
        # Determine if query is slow
        is_slow_query = query_log.mean_exec_time > settings.slow_query_threshold_ms
        
        # Create feature instance
        feature = QueryFeature(
            query_id=query_log.id,
            num_joins=query_features["num_joins"],
            has_select_star=query_features["has_select_star"],
            has_where_clause=query_features["has_where_clause"],
            num_subqueries=query_features["num_subqueries"],
            scan_types=plan_features.get("scan_types", []),
            indexed_tables_pct=self._calculate_indexed_tables_pct(plan_features),
            avg_table_size_mb=self._estimate_table_size(plan_features),
            is_slow_query=is_slow_query,
            complexity_score=query_features["complexity_score"]
        )
        
        session.add(feature)
        await session.commit()
        
        return feature
    
    def _count_joins(self, query_text: str) -> int:
        """Count the number of JOIN clauses in the query."""
        # Case insensitive search for JOIN keywords
        join_pattern = r'\b(?:INNER\s+)?JOIN\b|\bLEFT\s+JOIN\b|\bRIGHT\s+JOIN\b|\bFULL\s+JOIN\b'
        matches = re.findall(join_pattern, query_text.upper())
        return len(matches)
    
    def _has_select_star(self, query_text: str) -> bool:
        """Check if query uses SELECT *."""
        # Look for SELECT * pattern, accounting for whitespace
        pattern = r'SELECT\s+\*\s+FROM'
        return bool(re.search(pattern, query_text.upper()))
    
    def _has_where_clause(self, query_text: str) -> bool:
        """Check if query has a WHERE clause."""
        return "WHERE" in query_text.upper()
    
    def _count_subqueries(self, query_text: str) -> int:
        """Count the number of subqueries in the query."""
        # Count opening parentheses that likely indicate subqueries
        # This is a simplified approach
        open_parens = query_text.count('(')
        close_parens = query_text.count(')')
        # Rough estimate: assume balanced parentheses and count subqueries
        return max(0, (open_parens + close_parens) // 2 - 1)
    
    def _count_tables(self, query_text: str) -> int:
        """Count the number of tables referenced in the query."""
        # Extract table names from FROM and JOIN clauses
        from_pattern = r'FROM\s+(\w+)'
        join_pattern = r'JOIN\s+(\w+)'
        
        from_tables = re.findall(from_pattern, query_text.upper())
        join_tables = re.findall(join_pattern, query_text.upper())
        
        all_tables = set(from_tables + join_tables)
        return len(all_tables)
    
    def _has_aggregate_functions(self, query_text: str) -> bool:
        """Check if query uses aggregate functions."""
        aggregate_patterns = [
            r'\bCOUNT\b', r'\bSUM\b', r'\bAVG\b', r'\bMAX\b', r'\bMIN\b'
        ]
        
        for pattern in aggregate_patterns:
            if re.search(pattern, query_text.upper()):
                return True
        
        return False
    
    def _calculate_complexity_score(self, query_text: str) -> float:
        """Calculate a complexity score for the query."""
        score = 0.0
        
        # Base score from query length
        score += min(len(query_text) / 1000, 1.0)
        
        # Add points for complex features
        if self._count_joins(query_text) > 0:
            score += 0.2
        if self._count_subqueries(query_text) > 0:
            score += 0.3
        if self._has_aggregate_functions(query_text):
            score += 0.1
        if "UNION" in query_text.upper():
            score += 0.2
        if "EXISTS" in query_text.upper() or "IN" in query_text.upper():
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_indexed_tables_pct(self, plan_features: Dict[str, Any]) -> float:
        """Calculate percentage of tables that have indexes."""
        tables = plan_features.get("tables_scanned", [])
        indexes = plan_features.get("indexes_used", [])
        
        if not tables:
            return 0.0
        
        # Simplified calculation: assume tables with index scans have indexes
        indexed_tables = len([t for t in tables if any(t in idx for idx in indexes)])
        return (indexed_tables / len(tables)) * 100.0
    
    def _estimate_table_size(self, plan_features: Dict[str, Any]) -> float:
        """Estimate average table size based on plan features."""
        # This is a placeholder implementation
        # In a real system, you'd query table statistics
        return 10.0  # Default 10MB estimate


# Global instance
feature_extractor = FeatureExtractor() 