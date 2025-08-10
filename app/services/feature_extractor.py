import re
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

import sqlglot
from sqlglot import exp, parse_one

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
        Extract features from SQL query text using SQL AST when possible,
        falling back to regex heuristics if parsing fails.
        """
        tree = self._try_parse_sql(query_text)

        num_joins = self._count_joins_ast(query_text, tree)
        has_select_star = self._has_select_star_ast(query_text, tree)
        has_where_clause = self._has_where_clause_ast(query_text, tree)
        num_subqueries = self._count_subqueries_ast(tree, query_text)
        num_tables = self._count_tables_ast(tree, query_text)
        has_aggregate = self._has_aggregate_functions_ast(tree, query_text)

        features = {
            "num_joins": num_joins,
            "has_select_star": has_select_star,
            "has_where_clause": has_where_clause,
            "num_subqueries": num_subqueries,
            "query_length": len(query_text),
            "num_tables": num_tables,
            "has_order_by": "ORDER BY" in query_text.upper(),
            "has_group_by": "GROUP BY" in query_text.upper(),
            "has_having": "HAVING" in query_text.upper(),
            "has_limit": "LIMIT" in query_text.upper(),
            "has_distinct": "DISTINCT" in query_text.upper(),
            "has_aggregate": has_aggregate,
            "complexity_score": self._calculate_complexity_score_with_ast(
                query_text, num_joins, num_subqueries, has_aggregate
            ),
        }

        return features

    def extract_plan_features(self, plan_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """(unchanged) Extract features from execution plan analysis."""
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
        Build QueryFeature using AST-based extraction for the SQL text and
        PostgreSQL lookups for table sizes/indexes (async DB queries).
        """
        # Query features (AST-based where possible)
        query_features = self.extract_query_features(query_log.query_text)

        # Plan features if available
        plan_features: Dict[str, Any] = {}
        if execution_plan:
            plan_node = plan_parser.parse_plan_json(execution_plan.plan_json)
            plan_analysis = plan_parser.analyze_plan(plan_node)
            plan_features = self.extract_plan_features(plan_analysis)

        is_slow_query = query_log.mean_exec_time > settings.slow_query_threshold_ms

        # Async DB-driven metrics (if plan_features has tables_scanned)
        indexed_tables_pct = await self._calculate_indexed_tables_pct(session, plan_features)
        avg_table_size_mb = await self._estimate_table_size(session, plan_features)

        feature = QueryFeature(
            query_id=query_log.id,
            num_joins=query_features["num_joins"],
            has_select_star=query_features["has_select_star"],
            has_where_clause=query_features["has_where_clause"],
            num_subqueries=query_features["num_subqueries"],
            scan_types=plan_features.get("scan_types", []),
            indexed_tables_pct=indexed_tables_pct,
            avg_table_size_mb=avg_table_size_mb,
            is_slow_query=is_slow_query,
            complexity_score=query_features["complexity_score"]
        )

        session.add(feature)
        await session.commit()
        return feature

    # -----------------------
    # AST parsing utilities
    # -----------------------
    def _try_parse_sql(self, query_text: str) -> Optional[exp.Expression]:
        """
        Try to parse SQL into an AST using sqlglot. Return the root expression or None.
        We prefer the 'postgres' dialect but fall back to default parse on failure.
        """
        try:
            # parse_one handles single statements; use read='postgres' for dialect awareness
            return parse_one(query_text, read="postgres")
        except Exception as e:
            logger.debug("sqlglot failed to parse SQL: %s. Falling back to regex heuristics.", e)
            return None

    # -----------------------
    # AST-based feature extractors with regex fallback
    # -----------------------
    def _count_joins_ast(self, query_text: str, tree: Optional[exp.Expression]) -> int:
        if tree:
            # Count explicit JOIN expressions
            return sum(1 for _ in tree.find_all(exp.Join))
        # fall back to regex count
        join_pattern = r'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b'
        return len(re.findall(join_pattern, query_text.upper()))

    def _has_select_star_ast(self, query_text: str, tree: Optional[exp.Expression]) -> bool:
        if tree:
            for star in tree.find_all(exp.Star):
                # ensure the star is part of a SELECT projection
                if any(node for node in star.walk() if isinstance(node, exp.Select)):
                    return True
            # simpler approach: look for Select with Star columns
            for select in tree.find_all(exp.Select):
                for proj in select.expressions:
                    if isinstance(proj, exp.Star):
                        return True
            return False
        # fallback regex
        return bool(re.search(r'SELECT\s*\*', query_text, flags=re.IGNORECASE))

    def _has_where_clause_ast(self, query_text: str, tree: Optional[exp.Expression]) -> bool:
        if tree:
            return any(True for _ in tree.find_all(exp.Where))
        return bool(re.search(r'\bWHERE\b', query_text, flags=re.IGNORECASE))

    def _count_subqueries_ast(self, tree: Optional[exp.Expression], query_text: str) -> int:
        """
        Count subqueries:
        - Prefer counting `Subquery` nodes and nested `Select` nodes.
        - If parse fails, fallback to a regex counting pattern like '(SELECT ...)'.
        """
        if tree:
            # Count explicit Subquery nodes
            subquery_count = sum(1 for _ in tree.find_all(exp.Subquery))
            # Count nested Select nodes (exclude top-level main select)
            select_count = sum(1 for _ in tree.find_all(exp.Select))
            if select_count > 0:
                nested_selects = max(0, select_count - 1)
                subquery_count = max(subquery_count, nested_selects)
            return subquery_count

        # fallback regex: detects SELECT within parentheses
        return len(re.findall(r'\(\s*SELECT\b', query_text, flags=re.IGNORECASE))

    def _count_tables_ast(self, tree: Optional[exp.Expression], query_text: str) -> int:
        """
        Return number of unique referenced tables (schema-qualified preserved as 'schema.table').
        Use AST to detect Table nodes; fallback to regex extraction of FROM/JOIN tokens.
        """
        tables: Set[str] = set()
        if tree:
            for table in tree.find_all(exp.Table):
                try:
                    # sqlglot Table node may have .this or .name; sql() produces proper SQL snippet
                    sql_name = table.sql(dialect="postgres")
                    # normalize by removing extra quoting and whitespace
                    tables.add(sql_name.strip())
                except Exception:
                    # best effort: try attributes
                    if table.this:
                        tables.add(str(table.this))
            return len(tables)

        # fallback regex: capture simple identifiers (schema.table or table)
        from_pattern = r'FROM\s+([a-zA-Z_][\w\.]*)'
        join_pattern = r'JOIN\s+([a-zA-Z_][\w\.]*)'
        from_tables = re.findall(from_pattern, query_text, flags=re.IGNORECASE)
        join_tables = re.findall(join_pattern, query_text, flags=re.IGNORECASE)
        all_tables = set(from_tables + join_tables)
        return len(all_tables)

    def _has_aggregate_functions_ast(self, tree: Optional[exp.Expression], query_text: str) -> bool:
        if tree:
            # count occurrences of aggregate-like function nodes
            aggregates = {"COUNT", "SUM", "AVG", "MAX", "MIN"}
            for func in tree.find_all(exp.Anonymous):
                name = getattr(func, "name", None)
                if name and name.upper() in aggregates:
                    return True
            # sqlglot also models many built-ins as function expressions
            for func in tree.find_all(exp.Func):
                name = getattr(func, "this", None)
                # func.this may be an Identifier
                try:
                    fname = func.name.upper()
                except Exception:
                    fname = None
                if fname and fname in aggregates:
                    return True
            return False
        # fallback regex
        aggregate_patterns = [r'\bCOUNT\b', r'\bSUM\b', r'\bAVG\b', r'\bMAX\b', r'\bMIN\b']
        for pattern in aggregate_patterns:
            if re.search(pattern, query_text, flags=re.IGNORECASE):
                return True
        return False

    def _calculate_complexity_score_with_ast(
        self, query_text: str, num_joins: int, num_subqueries: int, has_aggregate: bool
    ) -> float:
        """
        Improved complexity score that uses AST-derived counts when available.
        Score between 0.0 and 1.0.
        """
        score = 0.0
        score += min(len(query_text) / 1000.0, 1.0)
        score += min(num_joins * 0.15, 0.4)         # each join adds weight
        score += min(num_subqueries * 0.25, 0.5)    # subqueries are costly
        if has_aggregate:
            score += 0.08
        if "UNION" in query_text.upper():
            score += 0.12
        if re.search(r'\bEXISTS\b|\bIN\s*\(', query_text, flags=re.IGNORECASE):
            score += 0.08
        return min(score, 1.0)

    # -----------------------
    # Postgres-backed async utilities
    # -----------------------
    async def _calculate_indexed_tables_pct(self, session: AsyncSession, plan_features: Dict[str, Any]) -> float:
        """
        Check pg_indexes for each scanned table and return % that have at least one index.
        plan_features['tables_scanned'] expected to be list like ['public.orders', 'schema.table'].
        """
        tables: List[str] = plan_features.get("tables_scanned", [])
        if not tables:
            return 0.0

        indexed_count = 0
        checked = 0
        for t in tables:
            # Normalize schema & table
            if "." in t:
                schema, table_name = t.split(".", 1)
            else:
                schema, table_name = "public", t
            checked += 1
            try:
                q = text(
                    "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = :schema AND tablename = :table_name"
                )
                res = await session.execute(q, {"schema": schema, "table_name": table_name})
                count = res.scalar() or 0
                if count > 0:
                    indexed_count += 1
            except Exception as e:
                logger.debug("Error when checking indexes for %s.%s: %s", schema, table_name, e)
                # ignore and continue

        if checked == 0:
            return 0.0
        return (indexed_count / checked) * 100.0

    async def _estimate_table_size(self, session: AsyncSession, plan_features: Dict[str, Any]) -> float:
        """
        Query pg_total_relation_size for each scanned table and return average size in MB.
        Uses pg_catalog.pg_tables to ensure table exists and quote identifiers.
        """
        tables: List[str] = plan_features.get("tables_scanned", [])
        if not tables:
            return 0.0

        total_mb = 0.0
        counted = 0
        for t in tables:
            if "." in t:
                schema, table_name = t.split(".", 1)
            else:
                schema, table_name = "public", t

            # Use format: pg_total_relation_size('schemaname.tablename') but prefer safe quoting via pg_namespace/pg_class lookup:
            try:
                # Find relid via pg_class/join with pg_namespace to avoid quoting issues
                relid_q = text(
                    """
                    SELECT pg_total_relation_size(c.oid)
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = :schema AND c.relname = :table_name
                    """
                )
                res = await session.execute(relid_q, {"schema": schema, "table_name": table_name})
                size_bytes = res.scalar() or 0
                size_mb = float(size_bytes) / (1024.0 * 1024.0)
                total_mb += size_mb
                counted += 1
            except Exception as e:
                logger.debug("Failed to fetch size for %s.%s: %s", schema, table_name, e)
                # ignore and continue

        if counted == 0:
            return 0.0
        return total_mb / counted


# Global instance
feature_extractor = FeatureExtractor()
