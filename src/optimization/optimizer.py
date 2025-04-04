import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from ..features.extraction import extract_features

class QueryOptimizer:
    def __init__(self, model_dir='data/models', performance_threshold=0.3):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.performance_threshold = performance_threshold
        
        # Try to load model, scaler, and performance metrics
        try:
            self.model = joblib.load(self.model_dir / 'random_forest_model.joblib')
            self.scaler = joblib.load(self.model_dir / 'scaler.joblib')
            self.metrics = joblib.load(self.model_dir / 'model_metrics.joblib')
            self.has_model = True
            self.model_performance = self.metrics.get('r2', -1)  # Default to -1 if not found
        except:
            print("No trained model found. Using heuristic predictions.")
            self.has_model = False
            self.model_performance = -1
    
    def predict_execution_time(self, features):
        """Predict execution time for a query."""
        # Extract features if string is provided
        if isinstance(features, str):
            features = extract_features(features)
        
        if self.has_model and self.model_performance >= self.performance_threshold:
            # Scale features
            X = pd.DataFrame([features])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            pred = self.model.predict(X_scaled)[0]
            return max(0, pred)
        else:
            # Use heuristic prediction based on query complexity
            base_complexity = features['query_complexity'] * 10
            
            # Add complexity factors
            complexity_factors = {
                'num_join': 20,
                'num_where': 5,
                'num_group_by': 15,
                'num_order_by': 10,
                'num_distinct': 8
            }
            
            # Calculate total complexity
            total_complexity = base_complexity
            for factor, weight in complexity_factors.items():
                total_complexity += features.get(factor, 0) * weight
            
            return total_complexity
    
    def get_optimization_suggestions(self, query, features):
        """Generate optimization suggestions based on query features."""
        suggestions = []
        
        # Check for SELECT *
        if 'SELECT *' in query.upper():
            suggestions.append("Specify needed columns instead of SELECT *")
        
        # Check for missing WHERE clause in JOIN queries
        if features.get('num_join', 0) > 0 and features.get('num_where', 0) == 0:
            suggestions.append("Add a WHERE clause to filter results")
        
        # Check for missing indexes on JOIN conditions
        if features.get('num_join', 0) > 0:
            suggestions.append("Consider adding indexes on JOIN columns")
        
        # Check for complex GROUP BY
        if features.get('num_group_by', 0) > 1:
            suggestions.append("Consider simplifying GROUP BY clause")
        
        # Check for missing LIMIT on large result sets
        if features.get('num_order_by', 0) > 0 and features.get('num_limit', 0) == 0:
            suggestions.append("Add LIMIT clause to prevent large result sets")
        
        return suggestions
    
    def optimize_query(self, query):
        """Analyze and optimize a query."""
        features = extract_features(query)
        return {
            'query': query,
            'predicted_time': self.predict_execution_time(features),
            'suggestions': self.get_optimization_suggestions(query, features)
        }

def main():
    # Example usage
    optimizer = QueryOptimizer()
    
    example_queries = [
        "SELECT * FROM users",
        "SELECT u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id",
        "SELECT id, name, email FROM users WHERE age > 25 AND status = 'active' ORDER BY created_at DESC LIMIT 10"
    ]
    
    for query in example_queries:
        print("\nAnalyzing query:", query)
        results = optimizer.optimize_query(query)
        
        print(f"Predicted Execution Time: {results['predicted_time']:.2f}ms")
        print("\nOptimization Suggestions:")
        for suggestion in results['suggestions']:
            print(f"- {suggestion}")
        print("-" * 80)

if __name__ == "__main__":
    main() 