import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import logging
from pathlib import Path
import json

class ETLPipeline:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("QueryIQ ETL Pipeline") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_data(self, source_path, file_type='csv'):
        """Load data from various sources."""
        try:
            if file_type == 'csv':
                df = pd.read_csv(source_path)
            elif file_type == 'json':
                df = pd.read_json(source_path)
            elif file_type == 'parquet':
                df = pd.read_parquet(source_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            self.logger.info(f"Successfully loaded data from {source_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def clean_data(self, df):
        """Clean and preprocess the data."""
        try:
            # Remove duplicates
            df = df.drop_duplicates()
            
            # Handle missing values
            df = df.fillna({
                'numeric_columns': df.mean(),
                'categorical_columns': df.mode().iloc[0]
            })
            
            # Remove outliers using IQR method
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[~((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR)))]
            
            self.logger.info("Data cleaning completed successfully")
            return df
        except Exception as e:
            self.logger.error(f"Error cleaning data: {str(e)}")
            raise

    def transform_data(self, df):
        """Transform the data for analysis."""
        try:
            # Feature engineering
            df['query_complexity'] = df['query_length'] * df['join_count']
            
            # Create time-based features
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            # Normalize numeric features
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = (df[numeric_columns] - df[numeric_columns].mean()) / df[numeric_columns].std()
            
            self.logger.info("Data transformation completed successfully")
            return df
        except Exception as e:
            self.logger.error(f"Error transforming data: {str(e)}")
            raise

    def save_data(self, df, output_path, file_type='parquet'):
        """Save processed data."""
        try:
            if file_type == 'parquet':
                df.to_parquet(output_path)
            elif file_type == 'csv':
                df.to_csv(output_path, index=False)
            elif file_type == 'json':
                df.to_json(output_path, orient='records')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            self.logger.info(f"Successfully saved data to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise

    def run_pipeline(self, input_path, output_path):
        """Run the complete ETL pipeline."""
        try:
            # Load data
            df = self.load_data(input_path)
            
            # Clean data
            df_cleaned = self.clean_data(df)
            
            # Transform data
            df_transformed = self.transform_data(df_cleaned)
            
            # Save processed data
            self.save_data(df_transformed, output_path)
            
            self.logger.info("ETL pipeline completed successfully")
        except Exception as e:
            self.logger.error(f"ETL pipeline failed: {str(e)}")
            raise
        finally:
            self.spark.stop()

def main():
    # Initialize pipeline
    pipeline = ETLPipeline()
    
    # Define paths
    input_path = "data/raw/query_data.csv"
    output_path = "data/processed/processed_data.parquet"
    
    # Run pipeline
    pipeline.run_pipeline(input_path, output_path)

if __name__ == "__main__":
    main() 