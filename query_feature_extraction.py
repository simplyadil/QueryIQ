import re
import pandas as pd

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
    
    for feature, pattern in keywords.items():
        # Using re.findall for precise counting
        matches = re.findall(pattern, q)
        features[feature] = len(matches)
    
    return features

# Example usage:
if __name__ == "__main__":
    sample_query = "SELECT DISTINCT s.name FROM sets s JOIN themes t ON s.theme_id = t.id WHERE s.year > 2015 LIMIT 50;"
    feats = extract_features(sample_query)
    print("Extracted features:")
    for key, value in feats.items():
        print(f"{key}: {value}")
