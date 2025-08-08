# QueryIQ - AI-powered SQL Query Optimization Assistant

QueryIQ is an intelligent SQL query optimization assistant that monitors PostgreSQL queries using `pg_stat_statements`, extracts features from SQL and EXPLAIN plans, and uses both heuristics and ML to suggest query improvements.

## 🎯 Features

- **Query Monitoring**: Collects query statistics from `pg_stat_statements`
- **Plan Analysis**: Parses and analyzes PostgreSQL EXPLAIN plans
- **Feature Extraction**: Extracts structural and performance features from queries
- **Rule Engine**: Applies heuristics and rules for optimization suggestions
- **ML Predictions**: Uses machine learning to predict query performance
- **REST API**: Complete FastAPI backend with comprehensive endpoints
- **Real-time Analysis**: Provides instant feedback on query performance

## 🏗️ Architecture

```
QueryIQ Backend/
├── app/
│   ├── api/routes/          # FastAPI route handlers
│   ├── core/               # Configuration and logging
│   ├── db/                 # Database session management
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic data validation
│   ├── services/           # Business logic services
│   └── main.py            # FastAPI application entry point
├── tests/                  # Unit and integration tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with `pg_stat_statements` extension enabled
- Local PostgreSQL instance running

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd QueryIQ
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your PostgreSQL connection details
   ```

5. **Initialize database**
   ```bash
   python -m app.db.init_db
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📊 Database Models

### QueryLog
Stores query execution statistics from `pg_stat_statements`:
- `id`: UUID primary key
- `query_text`: SQL query text
- `query_hash`: Hash for query identification
- `db_user`: Database user
- `database_name`: Database name
- `total_exec_time`: Total execution time
- `mean_exec_time`: Mean execution time
- `calls`: Number of executions
- `collected_at`: Collection timestamp

### ExecutionPlan
Stores parsed EXPLAIN plan data:
- `id`: UUID primary key
- `query_id`: Foreign key to QueryLog
- `plan_json`: JSON representation of EXPLAIN plan
- `total_cost`: Plan cost
- `actual_time`: Actual execution time
- `plan_depth`: Plan tree depth

### QueryFeature
Stores extracted features for ML analysis:
- `id`: UUID primary key
- `query_id`: Foreign key to QueryLog
- `num_joins`: Number of JOIN clauses
- `has_select_star`: Uses SELECT *
- `has_where_clause`: Has WHERE clause
- `num_subqueries`: Number of subqueries
- `scan_types`: Types of scans used
- `indexed_tables_pct`: Percentage of indexed tables
- `is_slow_query`: Performance indicator

### Suggestion
Stores optimization suggestions:
- `id`: UUID primary key
- `query_id`: Foreign key to QueryLog
- `suggestion_type`: Type of suggestion
- `message`: Human-readable message
- `confidence`: Confidence score (0.0-1.0)
- `source`: Source of suggestion
- `estimated_improvement_ms`: Estimated time improvement

## 🔌 API Endpoints

### Queries
- `GET /api/v1/queries/` - List all queries with pagination
- `GET /api/v1/queries/slow` - Get slowest queries
- `GET /api/v1/queries/{query_id}` - Get specific query
- `POST /api/v1/queries/collect` - Manually collect queries
- `GET /api/v1/queries/hash/{query_hash}` - Get query by hash

### Suggestions
- `GET /api/v1/suggestions/{query_id}` - Get suggestions for query
- `POST /api/v1/suggestions/{query_id}/generate` - Generate new suggestions
- `GET /api/v1/suggestions/{query_id}/count` - Get suggestion count
- `DELETE /api/v1/suggestions/{query_id}` - Delete suggestions

### Statistics
- `GET /api/v1/stats/overview` - System overview
- `GET /api/v1/stats/performance` - Performance statistics
- `GET /api/v1/stats/suggestions` - Suggestion statistics
- `GET /api/v1/stats/trends` - Trend analysis

### Machine Learning
- `POST /api/v1/ml/predict` - Predict execution time
- `GET /api/v1/ml/model/info` - Get model information
- `POST /api/v1/ml/model/load` - Load ML model
- `POST /api/v1/ml/model/train` - Train model
- `GET /api/v1/ml/features/extract` - Extract features

## 🧠 Services

### QueryCollector
- Reads from `pg_stat_statements`
- Collects slow queries above threshold
- Updates existing query statistics
- Provides query retrieval methods

### PlanParser
- Parses PostgreSQL EXPLAIN JSON output
- Extracts plan metrics and structure
- Analyzes scan types and join strategies
- Calculates plan complexity

### FeatureExtractor
- Extracts structural features from SQL
- Analyzes query complexity
- Processes execution plan features
- Creates feature vectors for ML

### RuleEngine
- Applies heuristic rules for suggestions
- Analyzes query structure patterns
- Identifies performance bottlenecks
- Generates optimization recommendations

### MLEngine
- Loads and manages ML models
- Predicts query execution time
- Generates ML-based suggestions
- Handles model training (placeholder)

## 🔧 Configuration

Environment variables in `.env`:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/queryiq
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:password@localhost:5432/queryiq
SECRET_KEY=your-secret-key-here
DEBUG=True
LOG_LEVEL=INFO
API_PREFIX=/api/v1
```

## 🧪 Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## 📈 Usage Examples

### 1. Collect Queries
```bash
curl -X POST http://localhost:8000/api/v1/queries/collect
```

### 2. Get Slow Queries
```bash
curl http://localhost:8000/api/v1/queries/slow?limit=10
```

### 3. Get Suggestions for Query
```bash
curl http://localhost:8000/api/v1/suggestions/{query_id}
```

### 4. Predict Query Performance
```bash
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "SELECT * FROM users WHERE email = ?",
    "features": {
      "num_joins": 0,
      "has_select_star": true,
      "has_where_clause": true
    }
  }'
```

### 5. Get System Statistics
```bash
curl http://localhost:8000/api/v1/stats/overview
```

## 🔍 API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Development

### Project Structure
```
QueryIQ/
├── app/
│   ├── api/routes/          # API endpoints
│   │   ├── queries.py      # Query management
│   │   ├── suggestions.py  # Suggestion endpoints
│   │   ├── stats.py        # Statistics endpoints
│   │   └── ml.py          # ML endpoints
│   ├── core/               # Core configuration
│   │   ├── config.py      # Settings management
│   │   └── logger.py      # Logging setup
│   ├── db/                 # Database layer
│   │   ├── session.py     # Async session management
│   │   └── init_db.py     # Database initialization
│   ├── models/             # SQLAlchemy models
│   │   ├── base.py        # Base model class
│   │   ├── query_log.py   # Query log model
│   │   ├── execution_plan.py # Plan model
│   │   ├── features.py    # Features model
│   │   └── suggestion.py  # Suggestion model
│   ├── schemas/            # Pydantic schemas
│   │   ├── query.py       # Query schemas
│   │   ├── plan.py        # Plan schemas
│   │   ├── feature.py     # Feature schemas
│   │   └── suggestion.py  # Suggestion schemas
│   ├── services/           # Business logic
│   │   ├── query_collector.py # Query collection
│   │   ├── plan_parser.py # Plan parsing
│   │   ├── feature_extractor.py # Feature extraction
│   │   ├── rule_engine.py # Rule-based suggestions
│   │   └── ml_engine.py   # ML predictions
│   └── main.py            # FastAPI app
├── tests/                  # Test suite
│   └── unit/              # Unit tests
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

### Adding New Features

1. **New API Endpoint**: Add route in `app/api/routes/`
2. **New Model**: Create in `app/models/` and add schema in `app/schemas/`
3. **New Service**: Add business logic in `app/services/`
4. **New Test**: Add test case in `tests/unit/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Ensure PostgreSQL and `pg_stat_statements` are properly configured
4. Verify database connection settings in `.env`

## 🔮 Future Enhancements

- [ ] Real ML model training and deployment
- [ ] Advanced query pattern recognition
- [ ] Automated index recommendation
- [ ] Query performance benchmarking
- [ ] Integration with monitoring tools
- [ ] Web-based dashboard
- [ ] Multi-database support
- [ ] Real-time query interception




