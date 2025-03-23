import re

def extract_features(query):
    """Extract features from a SQL query."""
    # If features are already extracted, return them
    if isinstance(query, dict):
        return query
        
    # Convert query to uppercase for case-insensitive matching
    q = query.upper()
    
    features = {}
    features['query_length'] = len(query)
    
    # Define keywords and use regex to count them
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
    
    # Calculate query complexity
    features['query_complexity'] = features['query_length'] * (features['num_join'] + 1)
    
    return features 