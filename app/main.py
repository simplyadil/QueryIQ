import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import logger
from app.db.session import init_db, close_db
from app.api.routes import queries, suggestions, stats, ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting QueryIQ application...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Load ML model
        from app.services.ml_engine import ml_engine
        await ml_engine.load_model()
        logger.info("ML model loaded successfully")
        
        logger.info("QueryIQ application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down QueryIQ application...")
    
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="QueryIQ",
    description="AI-powered SQL query optimization assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(
    queries.router,
    prefix=f"{settings.api_prefix}/queries",
    tags=["queries"]
)

app.include_router(
    suggestions.router,
    prefix=f"{settings.api_prefix}/suggestions",
    tags=["suggestions"]
)

app.include_router(
    stats.router,
    prefix=f"{settings.api_prefix}/stats",
    tags=["stats"]
)

app.include_router(
    ml.router,
    prefix=f"{settings.api_prefix}/ml",
    tags=["ml"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to QueryIQ - AI-powered SQL query optimization assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": settings.api_prefix
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"  # In reality, use actual timestamp
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 