import psycopg2
import json
from datetime import datetime
from ..features.extraction import extract_features
from ..models.training import train_model
from .optimizer import QueryOptimizer
from ..data.query_collector import QueryCollector

class QueryInterceptor:
    def __init__(self, config_path='config.json'):
        # Load database configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.collector = QueryCollector(config_path)
        self.optimizer = QueryOptimizer()
        
        # Initialize connection
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def intercept_query(self, query):
        """Intercept a query before execution."""
        try:
            # Extract features
            features = extract_features(query)
            
            # Predict execution time
            predicted_time = self.optimizer.predict_execution_time(features)
            
            # Get optimization suggestions
            suggestions = self.optimizer.get_optimization_suggestions(query, features)
            
            # Log the query for later analysis
            self.collector.log_query_performance(
                query=query,
                execution_time=predicted_time,
                resource_usage={}  # Will be updated after actual execution
            )
            
            return {
                'query': query,
                'predicted_time': predicted_time,
                'suggestions': suggestions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error intercepting query: {e}")
            raise
    
    def execute_query(self, query):
        """Execute a query and log its performance."""
        try:
            # Intercept query first
            analysis = self.intercept_query(query)
            
            # Execute query and measure time
            start_time = datetime.now()
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            execution_time = (datetime.now() - start_time).total_seconds() * 1000  # Convert to ms
            
            # Update performance log with actual execution time
            self.collector.log_query_performance(
                query=query,
                execution_time=execution_time,
                resource_usage={'actual_time': execution_time}
            )
            
            return {
                **analysis,
                'actual_time': execution_time,
                'results': results
            }
            
        except Exception as e:
            print(f"Error executing query: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
        self.collector.close()

def main():
    interceptor = QueryInterceptor()
    try:
        # Test queries
        test_queries = [
            "SELECT * FROM users",
            "SELECT u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id",
            "SELECT * FROM products WHERE category = 'electronics'"
        ]
        
        for query in test_queries:
            print(f"\nAnalyzing query: {query}")
            result = interceptor.execute_query(query)
            print(f"Predicted time: {result['predicted_time']:.2f}ms")
            print(f"Actual time: {result['actual_time']:.2f}ms")
            print("Suggestions:")
            for suggestion in result['suggestions']:
                print(f"- {suggestion}")
    finally:
        interceptor.close()

if __name__ == "__main__":
    main() 