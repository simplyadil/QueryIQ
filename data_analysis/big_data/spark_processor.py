from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
from pathlib import Path
import json
import time

class SparkProcessor:
    def __init__(self):
        # Initialize Spark session
        self.spark = SparkSession.builder \
            .appName("QueryIQ Big Data Processing") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "200") \
            .getOrCreate()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_data(self, data_path, format='parquet'):
        """Load data into Spark DataFrame."""
        try:
            if format == 'parquet':
                df = self.spark.read.parquet(data_path)
            elif format == 'csv':
                df = self.spark.read.csv(data_path, header=True, inferSchema=True)
            elif format == 'json':
                df = self.spark.read.json(data_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Successfully loaded data from {data_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def process_query_patterns(self, df):
        """Analyze query patterns using Spark."""
        try:
            # Register temporary view
            df.createOrReplaceTempView("queries")
            
            # Analyze query patterns
            patterns_df = self.spark.sql("""
                SELECT 
                    query_type,
                    COUNT(*) as query_count,
                    AVG(execution_time) as avg_execution_time,
                    MAX(execution_time) as max_execution_time,
                    MIN(execution_time) as min_execution_time,
                    AVG(resource_usage) as avg_resource_usage
                FROM queries
                GROUP BY query_type
                ORDER BY query_count DESC
            """)
            
            self.logger.info("Query pattern analysis completed")
            return patterns_df
        except Exception as e:
            self.logger.error(f"Error processing query patterns: {str(e)}")
            raise

    def analyze_performance_trends(self, df):
        """Analyze performance trends over time."""
        try:
            # Register temporary view
            df.createOrReplaceTempView("queries")
            
            # Analyze performance trends
            trends_df = self.spark.sql("""
                SELECT 
                    date_trunc('hour', timestamp) as hour,
                    query_type,
                    AVG(execution_time) as avg_execution_time,
                    AVG(resource_usage) as avg_resource_usage,
                    COUNT(*) as query_count
                FROM queries
                GROUP BY date_trunc('hour', timestamp), query_type
                ORDER BY hour, query_type
            """)
            
            self.logger.info("Performance trend analysis completed")
            return trends_df
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {str(e)}")
            raise

    def optimize_queries(self, df):
        """Identify optimization opportunities."""
        try:
            # Register temporary view
            df.createOrReplaceTempView("queries")
            
            # Identify slow queries
            slow_queries_df = self.spark.sql("""
                SELECT 
                    query_id,
                    query_text,
                    execution_time,
                    resource_usage,
                    query_type,
                    timestamp
                FROM queries
                WHERE execution_time > (
                    SELECT AVG(execution_time) + 2 * STDDEV(execution_time)
                    FROM queries
                )
                ORDER BY execution_time DESC
            """)
            
            self.logger.info("Query optimization analysis completed")
            return slow_queries_df
        except Exception as e:
            self.logger.error(f"Error optimizing queries: {str(e)}")
            raise

    def save_results(self, df, output_path, format='parquet'):
        """Save processed results."""
        try:
            if format == 'parquet':
                df.write.mode('overwrite').parquet(output_path)
            elif format == 'csv':
                df.write.mode('overwrite').csv(output_path, header=True)
            elif format == 'json':
                df.write.mode('overwrite').json(output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Successfully saved results to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            raise

    def run_analysis(self, input_path, output_dir):
        """Run complete big data analysis pipeline."""
        try:
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Load data
            df = self.load_data(input_path)
            
            # Process query patterns
            patterns_df = self.process_query_patterns(df)
            self.save_results(patterns_df, f"{output_dir}/query_patterns.parquet")
            
            # Analyze performance trends
            trends_df = self.analyze_performance_trends(df)
            self.save_results(trends_df, f"{output_dir}/performance_trends.parquet")
            
            # Optimize queries
            slow_queries_df = self.optimize_queries(df)
            self.save_results(slow_queries_df, f"{output_dir}/slow_queries.parquet")
            
            self.logger.info("Big data analysis completed successfully")
        except Exception as e:
            self.logger.error(f"Big data analysis failed: {str(e)}")
            raise
        finally:
            self.spark.stop()

def main():
    # Initialize processor
    processor = SparkProcessor()
    
    # Run analysis
    input_path = "data/processed/processed_data.parquet"
    output_dir = "data/big_data_analysis"
    processor.run_analysis(input_path, output_dir)

if __name__ == "__main__":
    main() 