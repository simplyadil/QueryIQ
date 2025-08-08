import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.logger import logger


@dataclass
class PlanNode:
    """Represents a node in the execution plan tree."""
    node_type: str
    total_cost: float
    actual_time: Optional[float] = None
    plan_rows: Optional[int] = None
    actual_rows: Optional[int] = None
    scan_type: Optional[str] = None
    join_type: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    children: List['PlanNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class PlanParser:
    """Service for parsing PostgreSQL EXPLAIN plan JSON output."""
    
    def parse_plan_json(self, plan_json: Dict[str, Any]) -> PlanNode:
        """
        Parse EXPLAIN JSON output into a structured PlanNode tree.
        
        Args:
            plan_json: JSON output from EXPLAIN (FORMAT JSON)
            
        Returns:
            Root PlanNode of the execution plan tree
        """
        try:
            if isinstance(plan_json, list):
                plan_json = plan_json[0]  # Take first plan if multiple
            
            return self._parse_node(plan_json)
            
        except Exception as e:
            logger.error(f"Error parsing plan JSON: {e}")
            raise
    
    def _parse_node(self, node_data: Dict[str, Any]) -> PlanNode:
        """Recursively parse a plan node and its children."""
        
        # Extract basic node information
        node_type = node_data.get("Node Type", "Unknown")
        total_cost = float(node_data.get("Total Cost", 0))
        actual_time = node_data.get("Actual Time")
        plan_rows = node_data.get("Plan Rows")
        actual_rows = node_data.get("Actual Rows")
        
        # Extract scan-specific information
        scan_type = None
        table_name = None
        index_name = None
        
        if "Scan" in node_type:
            scan_type = node_type
            table_name = node_data.get("Relation Name")
            index_name = node_data.get("Index Name")
        
        # Extract join-specific information
        join_type = None
        if "Join" in node_type:
            join_type = node_type
        
        # Create the node
        node = PlanNode(
            node_type=node_type,
            total_cost=total_cost,
            actual_time=actual_time,
            plan_rows=plan_rows,
            actual_rows=actual_rows,
            scan_type=scan_type,
            join_type=join_type,
            table_name=table_name,
            index_name=index_name
        )
        
        # Parse children recursively
        if "Plans" in node_data:
            for child_data in node_data["Plans"]:
                child_node = self._parse_node(child_data)
                node.children.append(child_node)
        
        return node
    
    def analyze_plan(self, plan_node: PlanNode) -> Dict[str, Any]:
        """
        Analyze a parsed plan and extract useful metrics.
        
        Args:
            plan_node: Root node of the parsed plan
            
        Returns:
            Dictionary containing plan analysis results
        """
        analysis = {
            "total_cost": plan_node.total_cost,
            "actual_time": plan_node.actual_time,
            "plan_depth": self._calculate_depth(plan_node),
            "scan_types": self._extract_scan_types(plan_node),
            "join_types": self._extract_join_types(plan_node),
            "has_sequential_scan": self._has_sequential_scan(plan_node),
            "has_index_scan": self._has_index_scan(plan_node),
            "estimated_rows": plan_node.plan_rows,
            "actual_rows": plan_node.actual_rows,
            "tables_scanned": self._extract_tables(plan_node),
            "indexes_used": self._extract_indexes(plan_node)
        }
        
        return analysis
    
    def _calculate_depth(self, node: PlanNode, current_depth: int = 0) -> int:
        """Calculate the maximum depth of the plan tree."""
        if not node.children:
            return current_depth
        
        max_depth = current_depth
        for child in node.children:
            child_depth = self._calculate_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _extract_scan_types(self, node: PlanNode) -> List[str]:
        """Extract all scan types used in the plan."""
        scan_types = []
        
        if node.scan_type:
            scan_types.append(node.scan_type)
        
        for child in node.children:
            scan_types.extend(self._extract_scan_types(child))
        
        return list(set(scan_types))  # Remove duplicates
    
    def _extract_join_types(self, node: PlanNode) -> List[str]:
        """Extract all join types used in the plan."""
        join_types = []
        
        if node.join_type:
            join_types.append(node.join_type)
        
        for child in node.children:
            join_types.extend(self._extract_join_types(child))
        
        return list(set(join_types))  # Remove duplicates
    
    def _has_sequential_scan(self, node: PlanNode) -> bool:
        """Check if the plan contains any sequential scans."""
        if node.scan_type and "Seq Scan" in node.scan_type:
            return True
        
        for child in node.children:
            if self._has_sequential_scan(child):
                return True
        
        return False
    
    def _has_index_scan(self, node: PlanNode) -> bool:
        """Check if the plan contains any index scans."""
        if node.scan_type and "Index Scan" in node.scan_type:
            return True
        
        for child in node.children:
            if self._has_index_scan(child):
                return True
        
        return False
    
    def _extract_tables(self, node: PlanNode) -> List[str]:
        """Extract all table names from the plan."""
        tables = []
        
        if node.table_name:
            tables.append(node.table_name)
        
        for child in node.children:
            tables.extend(self._extract_tables(child))
        
        return list(set(tables))  # Remove duplicates
    
    def _extract_indexes(self, node: PlanNode) -> List[str]:
        """Extract all index names from the plan."""
        indexes = []
        
        if node.index_name:
            indexes.append(node.index_name)
        
        for child in node.children:
            indexes.extend(self._extract_indexes(child))
        
        return list(set(indexes))  # Remove duplicates


# Global instance
plan_parser = PlanParser() 