import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from pathlib import Path
from ..features.extraction import extract_features

def train_model(data_path, output_dir):
    """Train and save the query execution time prediction model."""
    # Load and prepare data
    df = pd.read_parquet(data_path)
    
    # Extract features
    features_list = []
    for query in df['query_text']:
        features = extract_features(query)
        features_list.append(features)
    
    # Prepare data
    X = pd.DataFrame(features_list)
    y = df['execution_time']
    
    # Split and scale data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    metrics = {
        'mse': mean_squared_error(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred)
    }
    
    # Save model and scaler
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump(model, f"{output_dir}/random_forest_model.joblib")
    joblib.dump(scaler, f"{output_dir}/scaler.joblib")
    
    return metrics

if __name__ == "__main__":
    data_path = "data/processed/processed_data.parquet"
    output_dir = "data/models"
    metrics = train_model(data_path, output_dir)
    print("Model Training Results:")
    for metric, value in metrics.items():
        print(f"{metric.upper()}: {value:.4f}") 