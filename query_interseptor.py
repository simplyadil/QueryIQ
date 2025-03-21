import re
from flask import Flask, request, jsonify
import psycopg2
import pickle
import json

app = Flask(__name__)

with open("config.json", "r") as f:
    db_config = json.load(f)

# Load trained cost prediction model
with open("sql_cost_predictor.pkl", "rb") as f:
    model = pickle.load(f)

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
    q = query.upper()
    
    features = {}
    features['query_length'] = len(query)
    
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

def forward_query(query):
    """Executes the SQL query on the PostgreSQL database."""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return result

@app.route("/query", methods=["POST"])
def intercept_query():
    data = request.get_json()
    query = data.get("query")
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    features = extract_features(query)
    feature_vector = [features[k] for k in sorted(features.keys())]  # Ensure consistent order
    
    predicted_cost = model.predict([feature_vector])[0]
    
    result = forward_query(query)
    
    return jsonify({
        "predicted_cost": predicted_cost,
        "result": result
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
