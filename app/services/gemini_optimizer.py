import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
import json
import re
from dataclasses import dataclass
from datetime import datetime

from app.models.suggestion import Suggestion
from app.models.query_log import QueryLog
from app.core.logger import logger
from app.core.config import settings


@dataclass
class OptimizationResult:
    """Result of query optimization attempt."""
    original_query: str
    optimized_query: str
    optimization_type: str
    confidence: float
    explanation: str
    estimated_improvement: float


class GeminiQueryOptimizer:
    """AI-powered query optimizer using Google Gemini."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    async def optimize_query(
        self, 
        query: str, 
        suggestions: List[Suggestion],
        table_schemas: Dict[str, List[str]] = None
    ) -> OptimizationResult:
        """
        Use Gemini to rewrite a SQL query based on optimization suggestions.
        
        Args:
            query: Original SQL query
            suggestions: List of optimization suggestions
            table_schemas: Dict mapping table names to column lists
            
        Returns:
            OptimizationResult with optimized query and metadata
        """
        try:
            prompt = self._build_optimization_prompt(query, suggestions, table_schemas)
            
            response = self.model.generate_content(prompt)
            result = self._parse_gemini_response(response.text, query)
            
            logger.info(f"Gemini optimization completed with {result.confidence:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Gemini optimization failed: {e}")
            return OptimizationResult(
                original_query=query,
                optimized_query=query,  # Fallback to original
                optimization_type="FAILED",
                confidence=0.0,
                explanation=f"Optimization failed: {str(e)}",
                estimated_improvement=0.0
            )
    
    def _build_optimization_prompt(
        self, 
        query: str, 
        suggestions: List[Suggestion],
        table_schemas: Dict[str, List[str]] = None
    ) -> str:
        """Build the prompt for Gemini to optimize the query."""
        
        # Extract suggestion types and messages
        suggestion_text = "\n".join([
            f"- {s.suggestion_type}: {s.message}" 
            for s in suggestions
        ])
        
        # Include table schema information if available
        schema_text = ""
        if table_schemas:
            schema_text = "\nTable Schemas:\n"
            for table, columns in table_schemas.items():
                schema_text += f"- {table}: {', '.join(columns)}\n"
        
        prompt = f"""
You are a PostgreSQL query optimization expert. Optimize the following SQL query based on the provided suggestions.

ORIGINAL QUERY:
```sql
{query}
```

OPTIMIZATION SUGGESTIONS:
{suggestion_text}

{schema_text}

REQUIREMENTS:
1. Rewrite the query to address as many suggestions as possible
2. Ensure the optimized query produces the same result set
3. Focus on performance improvements like:
   - Replacing SELECT * with specific columns
   - Adding appropriate indexes (suggest CREATE INDEX statements)
   - Optimizing JOIN conditions
   - Improving WHERE clause efficiency
   - Converting subqueries to JOINs where beneficial

RESPONSE FORMAT (JSON):
{{
    "optimized_query": "-- Your optimized SQL query here",
    "optimization_type": "COMPREHENSIVE|INDEX|QUERY_REWRITE|JOIN_OPTIMIZATION",
    "confidence": 0.85,
    "explanation": "Detailed explanation of changes made",
    "estimated_improvement_pct": 35,
    "index_suggestions": [
        "CREATE INDEX idx_users_email ON users(email);",
        "CREATE INDEX idx_orders_user_id ON orders(user_id);"
    ],
    "changes_made": [
        "Replaced SELECT * with specific columns",
        "Added WHERE clause optimization",
        "Converted subquery to JOIN"
    ]
}}

Provide only the JSON response, no additional text.
"""
        return prompt
    
    def _parse_gemini_response(self, response_text: str, original_query: str) -> OptimizationResult:
        """Parse Gemini's JSON response into OptimizationResult."""
        try:
            # Clean the response text and extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            result = json.loads(json_match.group())
            
            return OptimizationResult(
                original_query=original_query,
                optimized_query=result.get('optimized_query', original_query),
                optimization_type=result.get('optimization_type', 'UNKNOWN'),
                confidence=float(result.get('confidence', 0.5)),
                explanation=result.get('explanation', 'No explanation provided'),
                estimated_improvement=float(result.get('estimated_improvement_pct', 0))
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return OptimizationResult(
                original_query=original_query,
                optimized_query=original_query,
                optimization_type="PARSE_ERROR",
                confidence=0.0,
                explanation=f"Failed to parse optimization response: {str(e)}",
                estimated_improvement=0.0
            )
    
    async def suggest_indexes(self, query: str, table_schemas: Dict[str, List[str]]) -> List[str]:
        """Generate index suggestions for a query."""
        prompt = f"""
Analyze this SQL query and suggest optimal indexes for PostgreSQL:

```sql
{query}
```

Table Schemas:
{json.dumps(table_schemas, indent=2)}

Return a JSON array of CREATE INDEX statements that would improve this query's performance:

["CREATE INDEX idx_example ON table(column);"]
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            logger.error(f"Index suggestion failed: {e}")
            return []


# Global instance - you'll need to set GEMINI_API_KEY in your settings
gemini_optimizer = GeminiQueryOptimizer(getattr(settings, 'gemini_api_key', ''))