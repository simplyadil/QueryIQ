import pandas as pd
from pathlib import Path

def process_data(input_path, output_path):
    """Process raw query data and save it for model training."""
    # Load data
    df = pd.read_csv(input_path)
    
    # Basic cleaning
    df = df.drop_duplicates()
    
    # Handle missing values
    numeric_columns = ['execution_time', 'resource_usage', 'query_length', 'join_count', 'table_count']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].mean())
    
    # Select needed columns
    df_processed = df[['query_text', 'execution_time']]
    
    # Save processed data
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_parquet(output_path)
    
    return df_processed

if __name__ == "__main__":
    input_path = "data/raw/query_data.csv"
    output_path = "data/processed/processed_data.parquet"
    df = process_data(input_path, output_path)
    print(f"Processed {len(df)} queries") 