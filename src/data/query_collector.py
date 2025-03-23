import psycopg2
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from src.features.extraction import extract_features

class QueryCollector:
    def __init__(self, config_path='config.json'):
        # Load database configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Create processed data directory if it doesn't exist
        Path('data/processed').mkdir(parents=True, exist_ok=True)
        
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
    
    def collect_query_data(self):
        """Collect query performance data from pg_stat_statements."""
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
            ORDER BY total_exec_time DESC;
            """
            
            df = pd.read_sql(query, self.conn)
            
            # Add timestamp
            df['timestamp'] = datetime.now()
            
            # Extract features for each query
            features_list = []
            for query_text in df['query']:
                features = extract_features(query_text)
                features_list.append(features)
            
            # Add features to dataframe
            features_df = pd.DataFrame(features_list)
            df = pd.concat([df, features_df], axis=1)
            
            # Save to parquet file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'data/processed/query_data_{timestamp}.parquet'
            df.to_parquet(output_path)
            
            print(f"Collected {len(df)} queries and saved to {output_path}")
            return df
            
        except Exception as e:
            print(f"Error collecting query data: {e}")
            raise
    
    def log_query_performance(self, query, execution_time, resource_usage):
        """Log a single query's performance data."""
        try:
            cursor = self.conn.cursor()
            
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
            
            # Execute insert
            cursor.execute(insert_query, (
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
            ))
            
            self.conn.commit()
            print(f"Logged performance data for query: {query[:100]}...")
            
        except Exception as e:
            print(f"Error logging query performance: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

def main():
    collector = QueryCollector()
    try:
        # Collect existing query data
        df = collector.collect_query_data()
        print("\nSample of collected data:")
        print(df.head())
    finally:
        collector.close()

if __name__ == "__main__":
    main() 