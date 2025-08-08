import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from src.features.extraction import extract_features
from .connection_manager import DatabaseConnectionManager

class QueryCollector:
    def __init__(self, config_path='config.json'):
        # Load database configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Create processed data directory if it doesn't exist
        Path('data/processed').mkdir(parents=True, exist_ok=True)
        
        # Initialize connection manager
        self.db_manager = DatabaseConnectionManager(config_path)
    
    def collect_query_data(self, batch_size=1000):
        """Collect query performance data from pg_stat_statements with batching."""
        try:
            query = """
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                shared_blks_hit,
                shared_blks_read,
                temp_blks_read,
                temp_blks_written
            FROM pg_stat_statements
            WHERE query NOT LIKE '%%pg_stat_statements%%'
            ORDER BY total_exec_time DESC
            LIMIT %s;
            """
            
            # Execute query with batching
            results = self.db_manager.execute_query(query, (batch_size,))
            
            if not results:
                print("No query data found")
                return None
            
            # Convert to DataFrame
            columns = ['query', 'calls', 'total_exec_time', 'mean_exec_time', 
                      'shared_blks_hit', 'shared_blks_read', 'temp_blks_read', 'temp_blks_written']
            df = pd.DataFrame(results, columns=columns)
            
            # Add timestamp
            df['timestamp'] = datetime.now()
            
            # Extract features efficiently using vectorized operations
            features_list = []
            for query_text in df['query']:
                features = extract_features(query_text)
                features_list.append(features)
            
            # Add features to dataframe
            features_df = pd.DataFrame(features_list)
            df = pd.concat([df, features_df], axis=1)
            
            # Save to parquet file with compression
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'data/processed/query_data_{timestamp}.parquet'
            df.to_parquet(output_path, compression='snappy')
            
            print(f"Collected {len(df)} queries and saved to {output_path}")
            return df
            
        except Exception as e:
            print(f"Error collecting query data: {e}")
            raise
    
    def log_query_performance(self, query, execution_time, resource_usage=None):
        """Log a single query's performance data efficiently."""
        try:
            # Extract features
            features = extract_features(query)
            
            # Convert numpy values to Python types
            exec_time = float(execution_time)
            
            # Prepare insert query
            insert_query = """
            INSERT INTO query_performance_log 
            (query, calls, total_exec_time, mean_exec_time, 
             shared_blks_hit, shared_blks_read, 
             temp_blks_read, temp_blks_written,
             query_length, num_select, num_from, num_where,
             num_join, num_group_by, num_order_by,
             num_distinct, num_limit, query_complexity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Execute insert using connection manager
            params = (
                query,
                1,  # calls
                exec_time,  # total_exec_time
                exec_time,  # mean_exec_time
                0,  # shared_blks_hit
                0,  # shared_blks_read
                0,  # temp_blks_read
                0,  # temp_blks_written
                int(features['query_length']),
                int(features['num_select']),
                int(features['num_from']),
                int(features['num_where']),
                int(features['num_join']),
                int(features['num_group_by']),
                int(features['num_order_by']),
                int(features['num_distinct']),
                int(features['num_limit']),
                int(features['query_complexity'])
            )
            
            self.db_manager.execute_query(insert_query, params)
            print(f"Logged performance data for query: {query[:100]}...")
            
        except Exception as e:
            print(f"Error logging query performance: {e}")
            raise
    
    def cleanup_old_data(self, days_to_keep=30):
        """Clean up old query performance data to prevent database bloat."""
        try:
            cleanup_query = """
            DELETE FROM query_performance_log 
            WHERE timestamp < NOW() - INTERVAL '%s days';
            """
            
            self.db_manager.execute_query(cleanup_query, (days_to_keep,))
            print(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
    
    def close(self):
        """Close database connection manager."""
        self.db_manager.close()

def main():
    collector = QueryCollector()
    try:
        # Collect existing query data
        df = collector.collect_query_data()
        if df is not None:
            print("\nSample of collected data:")
            print(df.head())
        
        # Clean up old data
        collector.cleanup_old_data()
    finally:
        collector.close()

if __name__ == "__main__":
    main() 