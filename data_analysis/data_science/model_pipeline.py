import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
import joblib
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

class ModelPipeline:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.models = {
            'random_forest': RandomForestRegressor(random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'xgboost': xgb.XGBRegressor(random_state=42)
        }
        
        # Initialize scaler
        self.scaler = StandardScaler()

    def load_data(self, data_path):
        """Load and prepare data for modeling."""
        try:
            # Load data
            df = pd.read_parquet(data_path)
            
            # Prepare features
            feature_columns = [
                'query_length', 'join_count', 'table_count',
                'query_complexity', 'hour', 'day_of_week'
            ]
            
            X = df[feature_columns]
            y = df['execution_time']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.logger.info("Data loaded and prepared successfully")
            return X_train_scaled, X_test_scaled, y_train, y_test
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def train_models(self, X_train, y_train):
        """Train multiple models with hyperparameter tuning."""
        try:
            trained_models = {}
            
            # Define parameter grids for each model
            param_grids = {
                'random_forest': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, 30, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
                'gradient_boosting': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 4, 5]
                },
                'xgboost': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.01, 0.1, 0.3],
                    'max_depth': [3, 4, 5]
                }
            }
            
            # Train each model
            for name, model in self.models.items():
                self.logger.info(f"Training {name}...")
                
                # Perform grid search
                grid_search = GridSearchCV(
                    model,
                    param_grids[name],
                    cv=5,
                    scoring='neg_mean_squared_error',
                    n_jobs=-1
                )
                
                grid_search.fit(X_train, y_train)
                trained_models[name] = grid_search.best_estimator_
                
                self.logger.info(f"Best parameters for {name}: {grid_search.best_params_}")
            
            return trained_models
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            raise

    def evaluate_models(self, trained_models, X_test, y_test):
        """Evaluate model performance."""
        try:
            results = {}
            
            for name, model in trained_models.items():
                # Make predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {
                    'mse': mse,
                    'rmse': rmse,
                    'r2': r2
                }
                
                self.logger.info(f"{name} Results:")
                self.logger.info(f"MSE: {mse:.4f}")
                self.logger.info(f"RMSE: {rmse:.4f}")
                self.logger.info(f"R2: {r2:.4f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error evaluating models: {str(e)}")
            raise

    def plot_feature_importance(self, trained_models, feature_names):
        """Plot feature importance for each model."""
        try:
            plt.figure(figsize=(15, 5))
            
            for i, (name, model) in enumerate(trained_models.items(), 1):
                plt.subplot(1, 3, i)
                
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                elif hasattr(model, 'coef_'):
                    importances = model.coef_
                else:
                    continue
                
                # Sort features by importance
                indices = np.argsort(importances)[::-1]
                
                plt.title(f'{name} Feature Importance')
                plt.bar(range(len(importances)), importances[indices])
                plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
                plt.tight_layout()
            
            plt.savefig('data/models/feature_importance.png')
            self.logger.info("Feature importance plots created successfully")
            
        except Exception as e:
            self.logger.error(f"Error plotting feature importance: {str(e)}")
            raise

    def save_models(self, trained_models, output_dir):
        """Save trained models."""
        try:
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Save models
            for name, model in trained_models.items():
                joblib.dump(model, f"{output_dir}/{name}_model.joblib")
            
            # Save scaler
            joblib.dump(self.scaler, f"{output_dir}/scaler.joblib")
            
            self.logger.info("Models saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
            raise

    def run_pipeline(self, data_path, output_dir):
        """Run complete model pipeline."""
        try:
            # Load and prepare data
            X_train, X_test, y_train, y_test = self.load_data(data_path)
            
            # Train models
            trained_models = self.train_models(X_train, y_train)
            
            # Evaluate models
            results = self.evaluate_models(trained_models, X_test, y_test)
            
            # Plot feature importance
            feature_names = [
                'query_length', 'join_count', 'table_count',
                'query_complexity', 'hour', 'day_of_week'
            ]
            self.plot_feature_importance(trained_models, feature_names)
            
            # Save models
            self.save_models(trained_models, output_dir)
            
            # Save results
            with open(f"{output_dir}/model_results.json", 'w') as f:
                json.dump(results, f, indent=4)
            
            self.logger.info("Model pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Model pipeline failed: {str(e)}")
            raise

def main():
    # Initialize pipeline
    pipeline = ModelPipeline()
    
    # Run pipeline
    data_path = "data/processed/processed_data.parquet"
    output_dir = "data/models"
    pipeline.run_pipeline(data_path, output_dir)

if __name__ == "__main__":
    main() 