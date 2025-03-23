# QueryIQ - Intelligent SQL Query Optimization

QueryIQ is a comprehensive SQL query optimization system that combines real-time query analysis, performance prediction, and visualization capabilities.

## Features

- **Real-time Query Interception**: Captures and analyzes queries before execution
- **Performance Prediction**: Predicts query execution time using machine learning
- **Optimization Suggestions**: Provides actionable recommendations for query improvement
- **Performance Monitoring**: Continuously collects and analyzes query performance data
- **PowerBI Integration**: Real-time visualization of query performance metrics

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 17 or higher
- PowerBI Desktop (for visualization)

## Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Database**:
Create a `config.json` file in the project root:
```json
{
    "dbname": "lego",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}
```

3. **Setup Database**:
```powershell
.\scripts\setup_database.ps1
```

4. **Run Demo**:
```bash
python demo.py
```

## Usage Modes

### 1. Demo Mode
```bash
python demo.py
```
This runs sample queries and shows optimization suggestions.

### 2. Monitoring Mode
```bash
python src/main.py
```
This starts continuous monitoring of your database queries.

### 3. Individual Query Analysis
```python
from src.main import QueryIQ

queryiq = QueryIQ()
result = queryiq.analyze_query("SELECT * FROM users WHERE age > 25")
print(f"Predicted time: {result['predicted_time']:.2f}ms")
print(f"Actual time: {result['actual_time']:.2f}ms")
print("Suggestions:")
for suggestion in result['suggestions']:
    print(f"- {suggestion}")
```

## Viewing Performance Dashboard

1. Open PowerBI Desktop
2. Click "Get Data" → "CSV"
3. Select `data/processed/query_performance.csv`
4. The dashboard will show:
   - Query Performance Over Time
   - Top 10 Slowest Queries
   - Query Complexity Analysis
   - Optimization Opportunities

## Project Structure

```
QueryIQ/
├── src/                    # Source code
├── scripts/               # Setup and utility scripts
├── data/                  # Data storage
│   ├── raw/              # Raw query data
│   └── processed/        # Processed data for visualization
├── logs/                  # System logs
├── config.json           # Database configuration
└── requirements.txt      # Python dependencies
```

## Troubleshooting

1. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check credentials in `config.json`
   - Ensure database exists

2. **PowerBI Issues**:
   - Verify PowerBI Desktop is installed
   - Check if data files exist in `data/processed/`
   - Ensure CSV file is not locked by another process

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---




