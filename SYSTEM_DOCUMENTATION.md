# QueryIQ - AI-Powered SQL Query Optimization System

## 🎯 **What is QueryIQ?**

QueryIQ is an intelligent SQL query optimization assistant that monitors PostgreSQL databases, analyzes query performance, and provides AI-powered suggestions to improve database performance. It combines real-time monitoring, machine learning predictions, and rule-based analysis to help database administrators and developers optimize their SQL queries.

## 🏗️ **System Architecture**

### **Backend (FastAPI + PostgreSQL)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   QueryIQ       │    │   React         │
│   Database      │◄──►│   Backend       │◄──►│   Frontend      │
│                 │    │   (FastAPI)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Core Components**

1. **Query Collector** - Monitors `pg_stat_statements` for query performance
2. **Plan Parser** - Analyzes PostgreSQL EXPLAIN plans
3. **Feature Extractor** - Extracts query characteristics for ML analysis
4. **Rule Engine** - Applies heuristics for optimization suggestions
5. **ML Engine** - Predicts query performance using machine learning
6. **REST API** - Provides endpoints for frontend communication
7. **Web Dashboard** - Modern React interface for system management

## 🔍 **How It Works**

### **1. Query Monitoring**
- **Source**: PostgreSQL `pg_stat_statements` extension
- **Collection**: Automatically gathers query execution statistics
- **Storage**: Stores query logs, execution plans, and performance metrics
- **Analysis**: Identifies slow queries and performance bottlenecks

### **2. Feature Extraction**
The system analyzes SQL queries and extracts features like:
- **Structural Features**: Number of JOINs, subqueries, WHERE clauses
- **Performance Indicators**: Query complexity, use of SELECT *
- **Plan Analysis**: Scan types, index usage, execution depth
- **Metadata**: Query hash, execution frequency, user context

### **3. Machine Learning Analysis**
- **Training Data**: Historical query performance data
- **Features**: Query structure, complexity, and characteristics
- **Predictions**: Expected execution time and performance impact
- **Confidence**: Model confidence scores for predictions

### **4. Optimization Suggestions**
The system provides suggestions in categories:
- **Query Rewrites**: Replace SELECT * with specific columns
- **Index Recommendations**: Add indexes for frequently queried columns
- **Performance Optimizations**: Break down complex queries
- **Configuration Changes**: Database parameter adjustments

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- PostgreSQL 12+ with `pg_stat_statements` extension
- Node.js 16+ (for frontend)
- Local PostgreSQL instance running

### **Installation Steps**

#### **1. Backend Setup**
```bash
# Clone and setup
cd QueryIQ
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
psql -U postgres -h localhost -c "CREATE DATABASE queryiq;"
psql -U postgres -h localhost -d queryiq -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

# Configuration
cp env.example .env
# Edit .env with your PostgreSQL connection details

# Initialize database
python -m app.db.init_db

# Start backend
uvicorn app.main:app --reload
```

#### **2. Frontend Setup**
```bash
cd frontend
npm install
npm start
```

### **Access Points**
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000

## 📊 **System Features**

### **Dashboard Overview**
- **Real-time Statistics**: Total queries, slow queries, suggestions count
- **Performance Metrics**: Average execution time, total execution time
- **Quick Actions**: Collect queries, view statistics, generate suggestions
- **System Health**: Backend connectivity and database status

### **Query Management**
- **Query Listing**: Paginated view of all collected queries
- **Performance Analysis**: Execution time, call frequency, total time
- **Query Details**: Full query text, metadata, and performance metrics
- **Manual Collection**: Trigger query collection from database

### **Optimization Suggestions**
- **Rule-based Suggestions**: Heuristic analysis of query patterns
- **ML-powered Recommendations**: AI-generated optimization advice
- **Confidence Scoring**: Reliability indicators for each suggestion
- **Implementation Cost**: Effort required to implement suggestions

### **Statistics & Analytics**
- **Performance Distribution**: Charts showing query execution time ranges
- **Slowest Queries**: Top performance bottlenecks
- **Trend Analysis**: Historical performance patterns
- **Suggestion Statistics**: Effectiveness of optimization recommendations

### **ML Predictions**
- **Query Analysis**: Real-time feature extraction from SQL
- **Performance Prediction**: Expected execution time estimates
- **Confidence Scoring**: Model reliability for predictions
- **Smart Suggestions**: AI-generated optimization recommendations

## 🔧 **API Endpoints**

### **Queries**
- `GET /api/v1/queries/` - List all queries with pagination
- `GET /api/v1/queries/slow` - Get slowest queries
- `GET /api/v1/queries/{query_id}` - Get specific query details
- `POST /api/v1/queries/collect` - Manually collect queries

### **Suggestions**
- `GET /api/v1/suggestions/{query_id}` - Get suggestions for query
- `POST /api/v1/suggestions/{query_id}/generate` - Generate new suggestions

### **Statistics**
- `GET /api/v1/stats/overview` - System overview statistics
- `GET /api/v1/stats/performance` - Performance metrics
- `GET /api/v1/stats/suggestions` - Suggestion effectiveness

### **Machine Learning**
- `POST /api/v1/ml/predict` - Predict query performance
- `GET /api/v1/ml/model/info` - Get model information
- `GET /api/v1/ml/features/extract` - Extract query features

## 💡 **Usage Examples**

### **1. Monitor Database Performance**
```bash
# Collect queries from database
curl -X POST http://localhost:8000/api/v1/queries/collect

# View system overview
curl http://localhost:8000/api/v1/stats/overview
```

### **2. Analyze Specific Query**
```bash
# Get query details
curl http://localhost:8000/api/v1/queries/{query_id}

# Get optimization suggestions
curl http://localhost:8000/api/v1/suggestions/{query_id}
```

### **3. Predict Query Performance**
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

### **4. Web Dashboard Usage**
1. **Dashboard**: View system overview and quick statistics
2. **Queries**: Browse all collected queries with performance metrics
3. **Suggestions**: View and generate optimization recommendations
4. **Statistics**: Analyze performance trends and distributions
5. **ML Predictions**: Test queries and get performance predictions

## 🧠 **How the AI Works**

### **Feature Extraction Process**
1. **SQL Parsing**: Analyze query structure and syntax
2. **Pattern Recognition**: Identify common optimization patterns
3. **Complexity Analysis**: Calculate query complexity scores
4. **Plan Analysis**: Extract execution plan characteristics

### **Machine Learning Pipeline**
1. **Data Collection**: Gather historical query performance data
2. **Feature Engineering**: Extract relevant query characteristics
3. **Model Training**: Train on performance patterns
4. **Prediction**: Estimate execution time for new queries
5. **Suggestion Generation**: Create optimization recommendations

### **Rule Engine Logic**
- **SELECT * Detection**: Identify queries using SELECT *
- **Missing WHERE Clauses**: Find queries without filtering
- **Complex JOIN Analysis**: Detect overly complex join patterns
- **Index Usage**: Analyze index utilization patterns
- **Performance Thresholds**: Flag queries exceeding time limits

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Database Connection**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify pg_stat_statements extension
psql -U postgres -d queryiq -c "SELECT * FROM pg_stat_statements LIMIT 1;"
```

#### **Backend Issues**
```bash
# Check logs
tail -f logs/queryiq.log

# Test database connection
python -c "from app.db.session import engine; print('DB OK')"
```

#### **Frontend Issues**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Verify API connectivity
curl http://localhost:8000/api/v1/stats/overview
```

### **Performance Optimization**
- **Database Indexing**: Add indexes for frequently queried columns
- **Query Optimization**: Rewrite complex queries
- **Configuration Tuning**: Adjust PostgreSQL parameters
- **Monitoring**: Set up alerts for slow queries

## 🔮 **Future Enhancements**

### **Planned Features**
- [ ] **Real-time Query Interception**: Monitor queries before execution
- [ ] **Advanced ML Models**: More sophisticated prediction algorithms
- [ ] **Automated Indexing**: Automatic index recommendation and creation
- [ ] **Query Pattern Recognition**: Identify common performance anti-patterns
- [ ] **Performance Benchmarking**: Compare query performance across environments
- [ ] **Integration APIs**: Connect with monitoring tools like Grafana
- [ ] **Multi-database Support**: Extend to MySQL, SQL Server, etc.
- [ ] **Web-based Query Editor**: Built-in SQL editor with suggestions

### **Advanced Analytics**
- [ ] **Trend Analysis**: Long-term performance tracking
- [ ] **Anomaly Detection**: Identify unusual query patterns
- [ ] **Capacity Planning**: Predict database growth needs
- [ ] **Cost Optimization**: Estimate query resource usage

## 📚 **Best Practices**

### **For Database Administrators**
1. **Regular Monitoring**: Set up automated query collection
2. **Performance Baselines**: Establish normal performance ranges
3. **Index Strategy**: Use suggestions to optimize indexing
4. **Query Reviews**: Regularly review and optimize slow queries

### **For Developers**
1. **Query Optimization**: Use SELECT specific columns instead of SELECT *
2. **Proper Indexing**: Add indexes for WHERE clause columns
3. **Query Complexity**: Break down complex queries into simpler ones
4. **Performance Testing**: Test queries before production deployment

### **For System Administrators**
1. **Resource Monitoring**: Monitor database server resources
2. **Backup Strategy**: Regular database backups
3. **Security**: Implement proper access controls
4. **Scaling**: Plan for database growth and scaling

## 🤝 **Contributing**

### **Development Setup**
```bash
# Backend development
cd QueryIQ
pip install -r requirements.txt
pytest tests/

# Frontend development
cd frontend
npm install
npm test
```

### **Code Structure**
```
QueryIQ/
├── app/                    # Backend application
│   ├── api/routes/        # API endpoints
│   ├── core/              # Configuration and logging
│   ├── db/                # Database models and sessions
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic data validation
│   ├── services/          # Business logic
│   └── main.py           # FastAPI application
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API service layer
│   │   └── types/        # TypeScript type definitions
│   └── public/           # Static assets
└── tests/                # Test suite
```

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

For issues and questions:
1. **Check Documentation**: Review this guide and API docs
2. **Verify Setup**: Ensure all prerequisites are met
3. **Check Logs**: Review application and database logs
4. **Test Connectivity**: Verify database and API connections
5. **Community**: Join our community for help and discussions

---

**QueryIQ** - Making database optimization intelligent and accessible! 🚀 