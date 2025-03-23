import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from ..features.extraction import extract_features

class QueryOptimizer:
    def __init__(self, model_dir='data/models'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to load model and scaler
        try:
            self.model = joblib.load(self.model_dir / 'random_forest_model.joblib')
            self.scaler = joblib.load(self.model_dir / 'scaler.joblib')
            self.has_model = True
        except:
            print("No trained model found. Using heuristic predictions.")
            self.has_model = False
    
    def predict_execution_time(self, features):
        """Predict execution time for a query."""
        # Extract features if string is provided
        if isinstance(features, str):
            features = extract_features(features)
        
        if self.has_model:
            # Scale features
            X = pd.DataFrame([features])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            pred = self.model.predict(X_scaled)[0]
            return max(0, pred)
        else:
            # Use heuristic prediction based on query complexity
            return features['query_complexity'] * 10  # Simple heuristic
    
    def get_optimization_suggestions(self, query, features=None):
        """Suggest query optimizations."""
        if features is None:
            features = extract_features(query)
            
        query_lower = query.lower()
        suggestions = []
        
        # Basic optimization rules
        if 'select *' in query_lower:
            suggestions.append("Specify needed columns instead of SELECT *")
        
        if features['num_where'] == 0:
            suggestions.append("Add a WHERE clause to filter results")
        
        if features['num_join'] > 2:
            suggestions.append("Consider breaking down complex JOINs")
        
        if features['num_order_by'] > 0:
            suggestions.append("Ensure proper indexes on ORDER BY columns")
        
        if features['num_group_by'] > 0:
            suggestions.append("Consider using materialized views for aggregations")
        
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