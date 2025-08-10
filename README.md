# QueryIQ - AI-powered SQL Query Optimization Assistant

QueryIQ is an intelligent backend service for monitoring, analyzing, and optimizing PostgreSQL queries. It leverages both heuristics and machine learning to provide actionable suggestions for query improvement.

## Features
- Collects query statistics from `pg_stat_statements`
- Parses and analyzes PostgreSQL EXPLAIN plans
- Extracts structural and performance features
- Applies rule-based and ML-driven optimization suggestions
- REST API built with FastAPI
- Real-time feedback on query performance

## Quick Start
1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd QueryIQ
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp env.example .env  # Edit .env for your DB
   python -m app.db.init_db
   uvicorn app.main:app --reload
   ```
2. **API would be available at**: http://localhost:8000

## Project Structure
```
app/
  api/routes/         # FastAPI endpoints (queries, suggestions, stats, ml)
  core/               # Config & logging
  db/                 # DB session & init
  models/             # SQLAlchemy ORM models
  schemas/            # Pydantic schemas
  services/           # Core business logic (feature extraction, ML, rules, etc)
  main.py             # FastAPI app entrypoint
scripts/              # Utility scripts
requirements.txt      # Dependencies
```

## Main Services
- **QueryCollector**: Reads from `pg_stat_statements`, collects and updates query stats
- **PlanParser**: Parses EXPLAIN JSON, extracts plan metrics
- **FeatureExtractor**: Extracts SQL and plan features for ML
- **RuleEngine**: Applies heuristics for suggestions
- **MLEngine**: Loads/trains ML models, predicts query performance

## API Overview
- `/api/v1/queries/` - List, get, collect, and search queries
- `/api/v1/suggestions/` - Generate and fetch suggestions
- `/api/v1/stats/` - System and performance stats
- `/api/v1/ml/` - ML model info, prediction, training

## Configuration
Set environment variables in `.env` (see `env.example`).

## Future
- Real ML model deployment
- Advanced pattern recognition
- Automated index recommendations
- Web dashboard & multi-DB support




