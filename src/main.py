import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from src.data.query_collector import QueryCollector
from src.optimization.query_interceptor import QueryInterceptor

class QueryIQ:
    def __init__(self, config_path='config.json', performance_threshold=0.3):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.collector = QueryCollector(config_path)
        self.interceptor = QueryInterceptor(config_path, performance_threshold=performance_threshold)
        
        # Create necessary directories
        Path('data/processed').mkdir(parents=True, exist_ok=True)
        Path('data/models').mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup efficient logging configuration."""
        log_file = Path('logs') / f'queryiq_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self, interval=300):  # 5 minutes default
        """Start monitoring query performance."""
        try:
            self.logger.info("Starting QueryIQ monitoring...")
            self.logger.info(f"Data will be collected every {interval} seconds")
            
            while True:
                try:
                    # Collect existing query data
                    self.collector.collect_query_data()
                    
                    # Clean up old data periodically
                    if datetime.now().hour == 2:  # Clean up at 2 AM
                        self.collector.cleanup_old_data()
                    
                    # Log status
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.logger.info(f"QueryIQ monitoring active at {timestamp}")
                    
                    # Wait for next interval
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Stopping QueryIQ monitoring...")
                    break
                except Exception as e:
                    self.logger.error(f"Error during monitoring: {e}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        finally:
            self.cleanup()
    
    def analyze_query(self, query):
        """Analyze a single query."""
        try:
            # Intercept and analyze query
            result = self.interceptor.execute_query(query)
            
            # Log analysis efficiently
            self.logger.info(f"Query analyzed: {query[:100]}... - Predicted: {result['predicted_time']:.2f}ms, Actual: {result['actual_time']:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            raise
    
    def train_model(self, data_path='data/processed/processed_data.parquet'):
        """Train the query execution time prediction model."""
        try:
            metrics = self.interceptor.train_model(data_path)
            
            # Log model training results
            self.logger.info(f"Model trained successfully with R² score: {metrics['r2']:.4f}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.collector.close()
            self.interceptor.close()
            self.logger.info("QueryIQ cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

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