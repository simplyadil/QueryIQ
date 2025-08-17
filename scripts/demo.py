#!/usr/bin/env python3
"""
Demo script to showcase QueryIQ's capabilities and generate sample benchmark results.
Run this to populate your database with realistic performance improvements.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.db.session import AsyncSessionLocal
from app.models.query_log import QueryLog
from app.models.suggestion import Suggestion
from app.services.benchmark_engine import benchmark_engine
from app.services.rule_engine import rule_engine
from app.core.logger import logger


class QueryIQDemo:
    """Demonstration class to showcase QueryIQ's capabilities."""
    
    def __init__(self):
        self.sample_queries = [
            {
                "query_text": "SELECT * FROM users WHERE email = 'test@example.com'",
                "mean_exec_time": 150.0,
                "calls": 25,
                "expected_improvement": 35.0
            },
            {
                "query_text": """
                SELECT u.name, COUNT(*) as order_count 
                FROM users u 
                JOIN orders o ON u.id = o.user_id 
                WHERE u.status = 'active'
                GROUP BY u.name
                """,
                "mean_exec_time": 420.0,
                "calls": 15,
                "expected_improvement": 28.5
            },
            {
                "query_text": """
                SELECT p.name, p.price, c.name as category 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.price > 100
                ORDER BY p.created_at DESC
                """,
                "mean_exec_time": 680.0,
                "calls": 8,
                "expected_improvement": 45.2
            },
            {
                "query_text": """
                SELECT * FROM orders 
                WHERE created_at >= '2024-01-01' 
                AND status IN ('pending', 'processing')
                """,
                "mean_exec_time": 890.0,
                "calls": 12,
                "expected_improvement": 52.1
            },
            {
                "query_text": """
                SELECT 
                    u.id,
                    u.name,
                    COUNT(o.id) as total_orders,
                    SUM(o.amount) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id, u.name
                HAVING COUNT(o.id) > 5
                """,
                "mean_exec_time": 1200.0,
                "calls": 6,
                "expected_improvement": 38.7
            }
        ]
    
    async def run_full_demo(self):
        """Run a complete demonstration of QueryIQ's capabilities."""
        print("🚀 Starting QueryIQ Demonstration...")
        print("=" * 60)
        
        async with AsyncSessionLocal() as session:
            # Step 1: Create sample queries
            queries = await self.create_sample_queries(session)
            print(f"✅ Created {len(queries)} sample queries")
            
            # Step 2: Generate suggestions for each query
            all_suggestions = []
            for query in queries:
                suggestions = await self.generate_suggestions_for_query(session, query)
                all_suggestions.extend(suggestions)
                print(f"💡 Generated {len(suggestions)} suggestions for query: {query.query_text[:50]}...")
            
            print(f"✅ Total suggestions generated: {len(all_suggestions)}")
            
            # Step 3: Run benchmarks (simulated for demo)
            benchmark_results = await self.run_demo_benchmarks(session, queries)
            print(f"⚡ Completed {len(benchmark_results)} benchmarks")
            
            # Step 4: Show results
            await self.display_results(session, benchmark_results)
            
            print("\n" + "=" * 60)
            print("🎉 Demo completed successfully!")
            print("\nYou can now:")
            print("- Open the dashboard: http://localhost:8000/dashboard")
            print("- Check API docs: http://localhost:8000/docs")
            print("- View benchmark results: http://localhost:8000/api/v1/benchmark/summary")
    
    async def create_sample_queries(self, session) -> list[QueryLog]:
        """Create sample query logs."""
        queries = []
        
        for i, sample in enumerate(self.sample_queries, 1):
            query_log = QueryLog(
                query_text=sample["query_text"].strip(),
                query_hash=f"demo_hash_{i}",
                db_user="demo_user",
                database_name="demo_db",
                total_exec_time=sample["mean_exec_time"] * sample["calls"],
                mean_exec_time=sample["mean_exec_time"],
                calls=sample["calls"]
            )
            
            session.add(query_log)
            queries.append(query_log)
        
        await session.commit()
        return queries
    
    async def generate_suggestions_for_query(self, session, query_log: QueryLog) -> list[Suggestion]:
        """Generate optimization suggestions for a query."""
        suggestions = []
        
        # Create rule-based suggestions based on query content
        query_text = query_log.query_text.upper()
        
        if "SELECT *" in query_text:
            suggestions.append(Suggestion(
                query_id=query_log.id,
                suggestion_type="QUERY_REWRITE",
                message="Replace SELECT * with specific column names to reduce data transfer",
                confidence=0.85,
                source="RULE_ENGINE",
                estimated_improvement_ms=query_log.mean_exec_time * 0.2,
                implementation_cost="LOW"
            ))
        
        if "JOIN" in query_text and "WHERE" in query_text:
            suggestions.append(Suggestion(
                query_id=query_log.id,
                suggestion_type="INDEX",
                message="Add indexes on JOIN and WHERE clause columns for better performance",
                confidence=0.78,
                source="RULE_ENGINE", 
                estimated_improvement_ms=query_log.mean_exec_time * 0.35,
                implementation_cost="MEDIUM"
            ))
        
        if query_log.mean_exec_time > 500:
            suggestions.append(Suggestion(
                query_id=query_log.id,
                suggestion_type="PERFORMANCE",
                message=f"Query execution time ({query_log.mean_exec_time:.1f}ms) is above recommended threshold",
                confidence=0.92,
                source="PERFORMANCE_ANALYZER",
                estimated_improvement_ms=query_log.mean_exec_time * 0.4,
                implementation_cost="HIGH"
            ))
        
        if "ORDER BY" in query_text:
            suggestions.append(Suggestion(
                query_id=query_log.id,
                suggestion_type="INDEX",
                message="Consider adding index on ORDER BY columns to avoid sorting",
                confidence=0.72,
                source="RULE_ENGINE",
                estimated_improvement_ms=query_log.mean_exec_time * 0.25,
                implementation_cost="MEDIUM"
            ))
        
        # Add ML-based suggestions
        if len(suggestions) > 0:
            suggestions.append(Suggestion(
                query_id=query_log.id,
                suggestion_type="ML_OPTIMIZATION",
                message="AI model recommends comprehensive query restructuring for optimal performance",
                confidence=0.81,
                source="ML_MODEL",
                estimated_improvement_ms=query_log.mean_exec_time * 0.3,
                implementation_cost="MEDIUM"
            ))
        
        # Save suggestions
        for suggestion in suggestions:
            session.add(suggestion)
        
        await session.commit()
        return suggestions
    
    async def run_demo_benchmarks(self, session, queries: list[QueryLog]) -> list[dict]:
        """Run simulated benchmarks for demo purposes."""
        results = []
        
        for i, query in enumerate(queries):
            sample_data = self.sample_queries[i]
            expected_improvement = sample_data["expected_improvement"]
            
            # Simulate benchmark results
            original_time = query.mean_exec_time
            optimized_time = original_time * (1 - expected_improvement / 100)
            improvement_ms = original_time - optimized_time
            
            # Create realistic optimized query
            optimized_query = self.create_optimized_query(query.query_text)
            
            # Store simulated benchmark result
            await self.store_demo_benchmark_result(session, {
                "query_id": str(query.id),
                "original_query": query.query_text,
                "optimized_query": optimized_query,
                "original_avg_ms": original_time,
                "optimized_avg_ms": optimized_time,
                "improvement_pct": expected_improvement,
                "improvement_ms": improvement_ms,
                "confidence": 0.75 + (i * 0.05),  # Varying confidence
                "optimization_type": "COMPREHENSIVE",
                "success": True
            })
            
            results.append({
                "query_id": query.id,
                "improvement_pct": expected_improvement,
                "improvement_ms": improvement_ms,
                "original_time": original_time,
                "optimized_time": optimized_time
            })
        
        return results
    
    def create_optimized_query(self, original_query: str) -> str:
        """Create a realistic optimized version of the query."""
        query = original_query
        
        # Replace SELECT * with specific columns
        if "SELECT *" in query:
            query = query.replace("SELECT *", "SELECT id, name, email")
        
        # Add LIMIT if not present and no aggregation
        if "LIMIT" not in query.upper() and "COUNT" not in query.upper() and "SUM" not in query.upper():
            query = query.rstrip(';') + " LIMIT 1000"
        
        # Optimize JOIN syntax
        if "LEFT JOIN" in query:
            query = query.replace("LEFT JOIN", "INNER JOIN")
        
        return query.strip()
    
    async def store_demo_benchmark_result(self, session, result_data: dict):
        """Store a demo benchmark result in the database."""
        from sqlalchemy import text
        
        # Create table if not exists
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
        
        # Insert result
        insert_query = text("""
            INSERT INTO performance_improvements (
                query_id, original_query, optimized_query, original_avg_ms,
                optimized_avg_ms, improvement_pct, improvement_ms, confidence,
                optimization_type, success
            ) VALUES (
                :query_id, :original_query, :optimized_query, :original_avg_ms,
                :optimized_avg_ms, :improvement_pct, :improvement_ms, :confidence,
                :optimization_type, :success
            )
        """)
        
        await session.execute(insert_query, result_data)
        await session.commit()
    
    async def display_results(self, session, benchmark_results: list[dict]):
        """Display a summary of the demo results."""
        print("\n📊 BENCHMARK RESULTS SUMMARY")
        print("-" * 50)
        
        total_queries = len(benchmark_results)
        total_improvement = sum(r["improvement_pct"] for r in benchmark_results)
        avg_improvement = total_improvement / total_queries if total_queries > 0 else 0
        
        total_time_saved = sum(r["improvement_ms"] for r in benchmark_results)
        
        print(f"Queries Optimized: {total_queries}")
        print(f"Average Improvement: {avg_improvement:.1f}%")
        print(f"Total Time Saved: {total_time_saved:.1f}ms ({total_time_saved/1000:.2f}s)")
        print(f"Best Improvement: {max(r['improvement_pct'] for r in benchmark_results):.1f}%")
        
        print(f"\n🎯 TOP OPTIMIZATIONS:")
        sorted_results = sorted(benchmark_results, key=lambda x: x["improvement_pct"], reverse=True)
        
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"{i}. {result['improvement_pct']:.1f}% faster ({result['improvement_ms']:.1f}ms saved)")
        
        # Get summary from database
        summary = await benchmark_engine.get_benchmark_summary(session)
        if summary:
            print(f"\n📈 DATABASE SUMMARY:")
            print(f"Success Rate: {summary.get('success_rate_pct', 0):.1f}%")
            print(f"Average Confidence: {summary.get('avg_confidence', 0):.2f}")


async def main():
    """Main demo function."""
    demo = QueryIQDemo()
    
    try:
        await demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}")


def run_quick_demo():
    """Quick demo that just populates some sample data."""
    print("🚀 Running Quick QueryIQ Demo...")
    print("This will create sample data to showcase the dashboard.")
    
    import time
    import random
    
    # Simulate creating benchmark results
    sample_improvements = [45.2, 28.7, 52.1, 34.8, 38.9, 41.3, 29.6, 47.8, 35.4, 42.1]
    
    print(f"✅ Generated {len(sample_improvements)} optimization results")
    print(f"📊 Average improvement: {sum(sample_improvements)/len(sample_improvements):.1f}%")
    print(f"🎯 Best improvement: {max(sample_improvements):.1f}%")
    print(f"⚡ Total time saved: {sum(sample_improvements) * 10:.1f}ms")
    
    print("\n🎉 Quick demo completed!")
    print("The full demo with database integration is available by running:")
    print("python scripts/demo.py --full")


if __name__ == "__main__":
    import sys
    
    if "--full" in sys.argv:
        # Run full database demo
        asyncio.run(main())
    else:
        # Run quick demo without database
        run_quick_demo()