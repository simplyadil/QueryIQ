from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.suggestion import PredictionRequest, PredictionResponse
from app.services.ml_engine import ml_engine
from app.services.feature_extractor import feature_extractor
from app.core.logger import logger

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_execution_time(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict execution time for a query using ML model.
    
    Args:
        request: Prediction request with query text and features
        db: Database session
        
    Returns:
        Prediction results with suggestions
    """
    try:
        # Extract features from query text if not provided
        if not request.features:
            request.features = feature_extractor.extract_query_features(request.query_text)
        
        # Make prediction
        prediction = await ml_engine.predict_execution_time(request.features)
        
        # Generate ML-based suggestions
        ml_suggestions = await ml_engine.generate_ml_suggestions(
            request.query_text,
            request.features,
            prediction["predicted_time_ms"]
        )
        
        return PredictionResponse(
            predicted_time_ms=prediction["predicted_time_ms"],
            confidence=prediction["confidence"],
            suggestions=ml_suggestions
        )
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to make prediction")


@router.get("/model/info")
async def get_model_info():
    """
    Get information about the current ML model.
    
    Returns:
        Model information
    """
    try:
        return await ml_engine.get_model_info()
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")


@router.post("/model/load")
async def load_model():
    """
    Manually load the ML model.
    
    Returns:
        Loading results
    """
    try:
        success = await ml_engine.load_model()
        
        if success:
            return {"message": "Model loaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to load model")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail="Failed to load model")


@router.post("/model/train")
async def train_model(
    training_data: list[Dict[str, Any]]
):
    """
    Train the ML model with new data.
    
    Args:
        training_data: List of training examples
        
    Returns:
        Training results
    """
    try:
        success = await ml_engine.train_model(training_data)
        
        if success:
            return {
                "message": "Model training completed successfully",
                "training_samples": len(training_data)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to train model")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail="Failed to train model")


@router.get("/features/extract")
async def extract_features(
    query_text: str
):
    """
    Extract features from a query text.
    
    Args:
        query_text: SQL query text
        
    Returns:
        Extracted features
    """
    try:
        features = feature_extractor.extract_query_features(query_text)
        
        return {
            "query_text": query_text,
            "features": features
        }
        
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract features") 