import pickle
import joblib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd


from app.models.suggestion import Suggestion
from app.core.logger import logger


@dataclass
class ModelMetrics:
    """Metrics for model performance evaluation."""
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    r2: float   # R-squared score
    cv_score: float  # Cross-validation score


class QueryPerformanceModel:
    """Real ML model for query performance prediction."""
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False
        self.metrics = None
        
        # Initialize the appropriate model
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> ModelMetrics:
        """
        Train the model on the provided data.
        
        Args:
            X: Feature matrix
            y: Target values (execution times)
            feature_names: List of feature names
            
        Returns:
            ModelMetrics with performance scores
        """

        self.feature_names = feature_names
        
        # Split data for training and validation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train the model
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True
        
        # Make predictions for evaluation
        y_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, 
            cv=5, scoring='neg_mean_absolute_error'
        )
        cv_score = -cv_scores.mean()
        
        self.metrics = ModelMetrics(mae, mse, rmse, r2, cv_score)
        
        logger.info(f"Model trained successfully. MAE: {mae:.2f}, R²: {r2:.3f}")
        return self.metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        Args:
            X: Feature matrix
            
        Returns:
            Predicted execution times
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_single(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Make a single prediction with confidence estimate.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (prediction, confidence)
        """
        # Convert features dict to array
        feature_array = np.array([
            [features.get(name, 0.0) for name in self.feature_names]
        ])
        
        prediction = self.predict(feature_array)[0]
        
        # Calculate confidence based on feature importance and model uncertainty
        confidence = self._calculate_confidence(features)
        
        return prediction, confidence
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """
        Calculate prediction confidence based on various factors.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Confidence score between 0 and 1
        """
        if not self.is_fitted or self.model_type != "random_forest":
            return 0.7  # Default confidence
        
        # For RandomForest, we can use prediction variance across trees
        feature_array = np.array([
            [features.get(name, 0.0) for name in self.feature_names]
        ])
        X_scaled = self.scaler.transform(feature_array)
        
        # Get predictions from all trees
        tree_predictions = np.array([
            tree.predict(X_scaled) for tree in self.model.estimators_
        ])
        
        # Calculate variance across tree predictions
        prediction_variance = np.var(tree_predictions)
        
        # Convert variance to confidence (inverse relationship)
        # Lower variance = higher confidence
        max_variance = 10000  # Adjust based on your data scale
        confidence = max(0.1, 1.0 - min(prediction_variance / max_variance, 0.9))
        
        return confidence
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores from the trained model."""
        if not self.is_fitted:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))
        return {}
    
    def save(self, filepath: str):
        """Save the trained model to disk."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'is_fitted': self.is_fitted,
            'metrics': self.metrics
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load a trained model from disk."""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.is_fitted = model_data['is_fitted']
        self.metrics = model_data.get('metrics')
        logger.info(f"Model loaded from {filepath}")


class MLEngine:
    """Service for machine learning predictions and model management."""
    
    def __init__(self):
        self.model = None
        self.model_path = "models/query_performance_model.pkl"
        self.feature_names = [
            "num_joins", "has_select_star", "has_where_clause", 
            "num_subqueries", "query_length", "num_tables", 
            "has_order_by", "has_group_by", "has_having", 
            "has_limit", "has_distinct", "has_aggregate", 
            "complexity_score", "total_cost", "plan_depth",
            "num_sequential_scans", "num_index_scans"
        ]
        
        # Ensure models directory exists
        Path("models").mkdir(exist_ok=True)
    
    async def load_model(self) -> bool:
        """
        Load the trained ML model from disk.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
           
            if os.path.exists(self.model_path):
                logger.info(f"Loading ML model from {self.model_path}")
                self.model = QueryPerformanceModel()
                self.model.load(self.model_path)
                logger.info("ML model loaded successfully")
                return True
            else:
                logger.warning(f"Model file {self.model_path} not found, creating new model")
                # Create a new model but don't train it yet
                self.model = QueryPerformanceModel()
                return True
                
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            return False
    
    async def predict_execution_time(
        self, 
        features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Predict query execution time using the ML model.
        
        Args:
            features: Dictionary of query features
            
        Returns:
            Dictionary with predicted time and confidence
        """
        if not self.model:
            await self.load_model()
        
        try:
            # Prepare features
            processed_features = self._prepare_features(features)
            
            # Make prediction
            predicted_time, confidence = self.model.predict_single(processed_features)
            
            return {
                "predicted_time_ms": float(predicted_time),
                "confidence": float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                "predicted_time_ms": 100.0,  # Default fallback
                "confidence": 0.5
            }
    
    def _prepare_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Prepare features for model input.
        
        Args:
            features: Raw feature dictionary
            
        Returns:
            Processed feature dictionary with all expected features
        """
        processed_features = {}
        
        # Ensure all expected features are present
        for feature_name in self.feature_names:
            if feature_name in features:
                value = features[feature_name]
                # Convert boolean to float
                if isinstance(value, bool):
                    processed_features[feature_name] = 1.0 if value else 0.0
                else:
                    processed_features[feature_name] = float(value)
            else:
                processed_features[feature_name] = 0.0
        
        return processed_features
    
    async def train_model(self, training_data: List[Dict[str, Any]]) -> bool:
        """
        Train the ML model with new data.
        
        Args:
            training_data: List of training examples with features and targets
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            if len(training_data) < 10:
                logger.warning(f"Insufficient training data: {len(training_data)} samples")
                return False
            
            logger.info(f"Training ML model with {len(training_data)} samples")
            
            # Prepare training data
            X_data = []
            y_data = []
            
            for example in training_data:
                features = self._prepare_features(example.get('features', {}))
                target = example.get('target', example.get('execution_time_ms', 0))
                
                feature_vector = [features[name] for name in self.feature_names]
                X_data.append(feature_vector)
                y_data.append(float(target))
            
            X = np.array(X_data)
            y = np.array(y_data)
            
            # Create new model if needed
            if not isinstance(self.model, QueryPerformanceModel):
                self.model = QueryPerformanceModel()
            
            # Train the model
            metrics = self.model.fit(X, y, self.feature_names)
            
            # Save the trained model
            self.model.save(self.model_path)
            
            logger.info(f"Model training completed successfully")
            logger.info(f"Model metrics - MAE: {metrics.mae:.2f}, R²: {metrics.r2:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return False
    
    async def generate_ml_suggestions(
        self, 
        query_text: str, 
        features: Dict[str, float],
        predicted_time: float
    ) -> List[Suggestion]:
        """
        Generate ML-based optimization suggestions.
        
        Args:
            query_text: SQL query text
            features: Query features
            predicted_time: Predicted execution time
            
        Returns:
            List of ML-generated suggestions
        """
        suggestions = []
        
        # Get feature importance if available
        feature_importance = {}
        if self.model and hasattr(self.model, 'get_feature_importance'):
            feature_importance = self.model.get_feature_importance()
        
        # High predicted time suggestion
        if predicted_time > 500:
            confidence = 0.9 if predicted_time > 1000 else 0.7
            suggestions.append(Suggestion(
                suggestion_type="ML_OPTIMIZATION",
                message=f"ML model predicts {predicted_time:.1f}ms execution time. Priority optimization needed.",
                confidence=confidence,
                source="ML_MODEL",
                estimated_improvement_ms=predicted_time * 0.4,
                implementation_cost="HIGH"
            ))
        
        # Feature-based suggestions using importance scores
        important_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        for feature_name, importance in important_features:
            if importance > 0.1 and features.get(feature_name, 0) > 0:
                suggestion = self._generate_feature_suggestion(
                    feature_name, features[feature_name], importance
                )
                if suggestion:
                    suggestions.append(suggestion)
        
        # Complexity-based suggestions
        complexity = features.get("complexity_score", 0)
        if complexity > 0.7:
            suggestions.append(Suggestion(
                suggestion_type="ML_QUERY_SIMPLIFICATION",
                message=f"ML analysis shows high query complexity ({complexity:.2f}). Consider breaking into simpler queries.",
                confidence=0.75,
                source="ML_MODEL",
                estimated_improvement_ms=predicted_time * 0.3,
                implementation_cost="MEDIUM"
            ))
        
        return suggestions
    
    def _generate_feature_suggestion(
        self, 
        feature_name: str, 
        feature_value: float, 
        importance: float
    ) -> Optional[Suggestion]:
        """Generate a suggestion based on a specific feature."""
        
        suggestions_map = {
            "has_select_star": Suggestion(
                suggestion_type="ML_QUERY_REWRITE",
                message="ML model identifies SELECT * as a major performance factor. Replace with specific columns.",
                confidence=0.8,
                source="ML_MODEL",
                estimated_improvement_ms=60.0,
                implementation_cost="LOW"
            ),
            "num_joins": Suggestion(
                suggestion_type="ML_INDEX",
                message=f"ML analysis shows {int(feature_value)} joins significantly impact performance. Ensure proper indexing on join columns.",
                confidence=0.75,
                source="ML_MODEL",
                estimated_improvement_ms=100.0 * feature_value,
                implementation_cost="MEDIUM"
            ),
            "num_sequential_scans": Suggestion(
                suggestion_type="ML_INDEX",
                message="ML model identifies sequential scans as primary bottleneck. Add indexes on filtered columns.",
                confidence=0.85,
                source="ML_MODEL",
                estimated_improvement_ms=200.0 * feature_value,
                implementation_cost="MEDIUM"
            ),
        }
        
        return suggestions_map.get(feature_name)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current ML model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "is_trained": bool(self.model and getattr(self.model, 'is_fitted', False)),
            "model_type": getattr(self.model, 'model_type', 'fallback') if self.model else 'none',
            "last_updated": datetime.utcnow().isoformat(),
            "features_used": self.feature_names,
            "model_file_exists": os.path.exists(self.model_path)
        }
        
        # Add metrics if available
        if self.model and hasattr(self.model, 'metrics') and self.model.metrics:
            metrics = self.model.metrics
            info["performance_metrics"] = {
                "mae": metrics.mae,
                "mse": metrics.mse,
                "rmse": metrics.rmse,
                "r2_score": metrics.r2,
                "cv_score": metrics.cv_score
            }
        
        # Add feature importance if available
        if self.model and hasattr(self.model, 'get_feature_importance'):
            info["feature_importance"] = self.model.get_feature_importance()
        
        return info


# Global instance
ml_engine = MLEngine()