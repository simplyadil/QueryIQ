import pandas as pd
import re

def extract_features(query):
    """
    Extracts simple metadata features from an SQL query string.
    
    Features include:
      - query_length: Number of characters in the query.
      - num_select: Occurrences of SELECT.
      - num_from: Occurrences of FROM.
      - num_where: Occurrences of WHERE.
      - num_join: Occurrences of JOIN.
      - num_group_by: Occurrences of GROUP BY.
      - num_order_by: Occurrences of ORDER BY.
      - num_distinct: Occurrences of DISTINCT.
      - num_limit: Occurrences of LIMIT.
    
    Returns a dictionary of features.
    """
    # Convert query to uppercase for case-insensitive matching
    q = query.upper()
    
    features = {}
    features['query_length'] = len(query)
    
    # Define keywords and use regex to count them accurately
    keywords = {
        'num_select': r'\bSELECT\b',
        'num_from': r'\bFROM\b',
        'num_where': r'\bWHERE\b',
        'num_join': r'\bJOIN\b',
        'num_group_by': r'\bGROUP\s+BY\b',
        'num_order_by': r'\bORDER\s+BY\b',
        'num_distinct': r'\bDISTINCT\b',
        'num_limit': r'\bLIMIT\b'
    }
    
    for feat, pattern in keywords.items():
        matches = re.findall(pattern, q)
        features[feat] = len(matches)
    
    return features

def build_combined_dataset(input_csv, output_csv):
    """
    Reads the raw training data CSV, extracts query features,
    and combines them with raw performance metrics.
    
    Assumes the input CSV has the columns:
      query, calls, total_exec_time, mean_exec_time,
      shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written, log_time
    """
    # Load the raw CSV dataset
    df_raw = pd.read_csv(input_csv)
    
    # List to hold combined features per query
    combined_features = []
    
    # Iterate over each row in the raw dataset
    for idx, row in df_raw.iterrows():
        query = row['query']
        # Extract query metadata features
        meta_features = extract_features(query)
        
        # Collect raw performance metrics (excluding log_time, if not needed as a feature)
        raw_features = {
            'calls': row['calls'],
            'total_exec_time': row['total_exec_time'],
            'mean_exec_time': row['mean_exec_time'],
            'shared_blks_hit': row['shared_blks_hit'],
            'shared_blks_read': row['shared_blks_read'],
            'temp_blks_read': row['temp_blks_read'],
            'temp_blks_written': row['temp_blks_written']
        }
        
        # Optionally, you can include log_time as a feature if it makes sense for your model
        # For now, we skip it.
        
        # Combine both dictionaries
        combined = {**meta_features, **raw_features}
        combined['query'] = query  # include the query text for reference if needed
        
        combined_features.append(combined)
    
    # Convert list of dicts to DataFrame
    df_combined = pd.DataFrame(combined_features)
    
    # Save the combined training dataset to a CSV file
    df_combined.to_csv(output_csv, index=False)
    print(f"Combined training dataset saved to {output_csv}")

if __name__ == "__main__":
    input_csv = "training_data.csv"  # Raw data CSV generated from performance logging
    output_csv = "combined_training_dataset.csv"  # Output CSV with both raw and extracted features
    build_combined_dataset(input_csv, output_csv)
