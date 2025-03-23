from src.main import QueryIQ

def main():
    # Initialize QueryIQ
    queryiq = QueryIQ()
    
    try:
        # Test queries
        test_queries = [
            "SELECT * FROM users",
            "SELECT u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id",
            "SELECT * FROM products WHERE category = 'electronics'"
        ]
        
        print("\n=== QueryIQ Demo ===")
        print("Testing query analysis and optimization...\n")
        
        # First run: Using heuristics (no model)
        print("Phase 1: Testing with heuristics (no model)")
        for query in test_queries:
            print(f"\nAnalyzing query: {query}")
            result = queryiq.analyze_query(query)
            print(f"Predicted time: {result['predicted_time']:.2f}ms")
            print(f"Actual time: {result['actual_time']:.2f}ms")
            print(f"Using model: {result['using_model']}")
            print("Optimization suggestions:")
            for suggestion in result['suggestions']:
                print(f"- {suggestion}")
            print("-" * 80)
        
        # Train model
        print("\nPhase 2: Training prediction model...")
        try:
            metrics = queryiq.train_model()
            print(f"Model trained successfully with R² score: {metrics['r2']:.4f}")
        except Exception as e:
            print(f"Error training model: {e}")
            print("Continuing with heuristic predictions...")
        
        # Second run: With model (if available)
        print("\nPhase 3: Testing with model (if available)")
        for query in test_queries:
            print(f"\nAnalyzing query: {query}")
            result = queryiq.analyze_query(query)
            print(f"Predicted time: {result['predicted_time']:.2f}ms")
            print(f"Actual time: {result['actual_time']:.2f}ms")
            print(f"Using model: {result['using_model']}")
            print("Optimization suggestions:")
            for suggestion in result['suggestions']:
                print(f"- {suggestion}")
            print("-" * 80)
        
        print("\nStarting monitoring mode (press Ctrl+C to stop)...")
        queryiq.start_monitoring(interval=60)  # 1 minute interval for testing
        
    except KeyboardInterrupt:
        print("\nStopping QueryIQ...")
    finally:
        queryiq.cleanup()

if __name__ == "__main__":
    main() 