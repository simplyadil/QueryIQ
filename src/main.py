import os
import json
import time
from datetime import datetime
from pathlib import Path
from src.data.query_collector import QueryCollector
from src.optimization.query_interceptor import QueryInterceptor
from src.visualization.powerbi_connector import PowerBIConnector

class QueryIQ:
    def __init__(self, config_path='config.json', performance_threshold=0.3):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.collector = QueryCollector(config_path)
        self.interceptor = QueryInterceptor(config_path, performance_threshold=performance_threshold)
        self.visualizer = PowerBIConnector()
        
        # Create necessary directories
        Path('data/processed').mkdir(parents=True, exist_ok=True)
        Path('data/models').mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self, interval=300):  # 5 minutes default
        """Start monitoring query performance."""
        try:
            print("Starting QueryIQ monitoring...")
            print(f"Data will be collected every {interval} seconds")
            
            while True:
                try:
                    # Collect existing query data
                    self.collector.collect_query_data()
                    
                    # Update visualizations
                    self.visualizer.update_visualizations()
                    
                    # Log status
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] QueryIQ monitoring active")
                    
                    # Wait for next interval
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    print("\nStopping QueryIQ monitoring...")
                    break
                except Exception as e:
                    print(f"Error during monitoring: {e}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        finally:
            self.cleanup()
    
    def analyze_query(self, query):
        """Analyze a single query."""
        try:
            # Intercept and analyze query
            result = self.interceptor.execute_query(query)
            
            # Log analysis
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'query': query,
                'predicted_time': result['predicted_time'],
                'actual_time': result['actual_time'],
                'suggestions': result['suggestions'],
                'using_model': result['using_model']
            }
            
            self._log_analysis(log_entry)
            
            return result
            
        except Exception as e:
            print(f"Error analyzing query: {e}")
            raise
    
    def train_model(self, data_path='data/processed/processed_data.parquet'):
        """Train the query execution time prediction model."""
        try:
            metrics = self.interceptor.train_model(data_path)
            
            # Log model training results
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'event': 'model_training',
                'metrics': metrics
            }
            
            self._log_analysis(log_entry)
            
            return metrics
            
        except Exception as e:
            print(f"Error training model: {e}")
            raise
    
    def _log_analysis(self, log_entry):
        """Log query analysis results."""
        try:
            log_file = Path('logs') / f'query_analysis_{datetime.now().strftime("%Y%m%d")}.json'
            
            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new log entry
            logs.append(log_entry)
            
            # Save updated logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Error logging analysis: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.collector.close()
            self.interceptor.close()
            print("QueryIQ cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")

def main():
    # Initialize QueryIQ
    queryiq = QueryIQ()
    
    try:
        # Test query analysis
        test_query = "SELECT * FROM users WHERE age > 25"
        print("\nAnalyzing test query...")
        result = queryiq.analyze_query(test_query)
        print(f"Predicted time: {result['predicted_time']:.2f}ms")
        print(f"Actual time: {result['actual_time']:.2f}ms")
        print(f"Using model: {result['using_model']}")
        print("Suggestions:")
        for suggestion in result['suggestions']:
            print(f"- {suggestion}")
        
        # Start monitoring
        print("\nStarting monitoring...")
        queryiq.start_monitoring(interval=60)  # 1 minute interval for testing
        
    except KeyboardInterrupt:
        print("\nStopping QueryIQ...")
    finally:
        queryiq.cleanup()

if __name__ == "__main__":
    main() 