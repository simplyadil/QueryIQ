#!/bin/bash

# Updated setup_database.sh for QueryIQ
echo "🚀 Starting QueryIQ Database Setup..."

# Configuration - use environment variables or defaults
DBNAME="${POSTGRES_DB:-queryiq}"
USER="${POSTGRES_USER:-postgres}"
PASSWORD="${POSTGRES_PASSWORD:-yourpassword}"
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"

# Check if we have a .env file to source
if [ -f ".env" ]; then
    echo "📄 Loading configuration from .env file..."
    export $(grep -v '^#' .env | xargs)
    
    # Extract database URL components if DATABASE_URL is set
    if [ ! -z "$DATABASE_URL" ]; then
        # Parse postgresql://user:password@host:port/dbname
        DBNAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
        USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        PASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    fi
fi

# Set password for psql
export PGPASSWORD="$PASSWORD"

echo "🔧 Database: $DBNAME on $HOST:$PORT as user $USER"

# Test connection
echo "🔍 Testing PostgreSQL connection..."
if ! psql -U "$USER" -h "$HOST" -p "$PORT" -d "postgres" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to PostgreSQL. Please check your configuration."
    echo "Make sure PostgreSQL is running and the credentials are correct."
    exit 1
fi

# Create database if it doesn't exist
echo "🗄️ Creating database '$DBNAME' if it doesn't exist..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "postgres" -c "CREATE DATABASE $DBNAME;" 2>/dev/null || echo "Database already exists"

# Create extensions
echo "🔌 Creating required extensions..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" || echo "pg_stat_statements extension creation failed (this is optional)"
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" || echo "uuid-ossp extension creation failed (using gen_random_uuid instead)"

# Create QueryIQ tables (matching your SQLAlchemy models)
echo "📊 Creating QueryIQ tables..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" << 'EOF'
-- Create query_logs table (matches QueryLog model)
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    db_user VARCHAR(100),
    database_name VARCHAR(100),
    total_exec_time FLOAT NOT NULL DEFAULT 0.0,
    mean_exec_time FLOAT NOT NULL DEFAULT 0.0,
    calls INTEGER NOT NULL DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for query_logs
CREATE INDEX IF NOT EXISTS idx_query_logs_hash ON query_logs(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_logs_text ON query_logs USING gin(to_tsvector('english', query_text));
CREATE INDEX IF NOT EXISTS idx_query_logs_mean_time ON query_logs(mean_exec_time);

-- Create execution_plans table (matches ExecutionPlan model)
CREATE TABLE IF NOT EXISTS execution_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_id UUID NOT NULL,
    plan_json JSONB NOT NULL,
    total_cost FLOAT,
    actual_time FLOAT,
    plan_depth INTEGER,
    plan_type VARCHAR(50)
);

-- Create index for execution_plans
CREATE INDEX IF NOT EXISTS idx_execution_plans_query_id ON execution_plans(query_id);

-- Create query_features table (matches QueryFeature model)
CREATE TABLE IF NOT EXISTS query_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_id UUID NOT NULL,
    num_joins INTEGER NOT NULL DEFAULT 0,
    has_select_star BOOLEAN NOT NULL DEFAULT FALSE,
    has_where_clause BOOLEAN NOT NULL DEFAULT FALSE,
    num_subqueries INTEGER NOT NULL DEFAULT 0,
    scan_types TEXT[],
    indexed_tables_pct FLOAT,
    avg_table_size_mb FLOAT,
    is_slow_query BOOLEAN NOT NULL DEFAULT FALSE,
    complexity_score FLOAT
);

-- Create index for query_features
CREATE INDEX IF NOT EXISTS idx_query_features_query_id ON query_features(query_id);

-- Create suggestions table (matches Suggestion model)
CREATE TABLE IF NOT EXISTS suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_id UUID NOT NULL,
    suggestion_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    source VARCHAR(50) NOT NULL,
    estimated_improvement_ms FLOAT,
    implementation_cost VARCHAR(20)
);

-- Create index for suggestions
CREATE INDEX IF NOT EXISTS idx_suggestions_query_id ON suggestions(query_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_type ON suggestions(suggestion_type);

-- Create performance_improvements table (for benchmarking)
CREATE TABLE IF NOT EXISTS performance_improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID,
    original_query TEXT,
    optimized_query TEXT,
    original_avg_ms FLOAT,
    optimized_avg_ms FLOAT,
    improvement_pct FLOAT,
    improvement_ms FLOAT,
    confidence FLOAT,
    optimization_type VARCHAR(100),
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance_improvements
CREATE INDEX IF NOT EXISTS idx_performance_improvements_query_id ON performance_improvements(query_id);
CREATE INDEX IF NOT EXISTS idx_performance_improvements_success ON performance_improvements(success);
CREATE INDEX IF NOT EXISTS idx_performance_improvements_created_at ON performance_improvements(created_at);
EOF

# Create sample tables for testing and demos
echo "🎯 Creating sample data tables..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" << 'EOF'
-- Create sample users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    age INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sample orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER,
    amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sample products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10,2),
    stock INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table for JOIN examples
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add some indexes for realistic performance testing
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
EOF

# Insert sample data
echo "📝 Inserting sample data..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" << 'EOF'
-- Insert sample users (more realistic data)
INSERT INTO users (name, email, age, status, last_login)
SELECT 
    'User ' || i,
    'user' || i || '@example.com',
    20 + (i % 50),
    CASE 
        WHEN i % 4 = 0 THEN 'active'
        WHEN i % 4 = 1 THEN 'inactive' 
        ELSE 'pending'
    END,
    CURRENT_TIMESTAMP - (i || ' days')::INTERVAL
FROM generate_series(1, 1000) i
ON CONFLICT DO NOTHING;

-- Insert sample categories
INSERT INTO categories (name, description)
VALUES 
    ('Electronics', 'Electronic devices and gadgets'),
    ('Clothing', 'Fashion and apparel'),
    ('Books', 'Books and educational materials'),
    ('Home', 'Home and garden items'),
    ('Sports', 'Sports and outdoor equipment')
ON CONFLICT DO NOTHING;

-- Insert sample products
INSERT INTO products (name, category, price, stock)
SELECT 
    'Product ' || i,
    CASE 
        WHEN i % 5 = 0 THEN 'Electronics'
        WHEN i % 5 = 1 THEN 'Clothing'
        WHEN i % 5 = 2 THEN 'Books'
        WHEN i % 5 = 3 THEN 'Home'
        ELSE 'Sports'
    END,
    (10.99 + (i % 500))::DECIMAL(10,2),
    50 + (i % 950)
FROM generate_series(1, 500) i
ON CONFLICT DO NOTHING;

-- Insert sample orders
INSERT INTO orders (user_id, product_id, amount, status)
SELECT 
    1 + (i % 1000),
    1 + (i % 500),
    (19.99 + (i % 200))::DECIMAL(10,2),
    CASE 
        WHEN i % 5 = 0 THEN 'completed'
        WHEN i % 5 = 1 THEN 'pending'
        WHEN i % 5 = 2 THEN 'processing'
        WHEN i % 5 = 3 THEN 'shipped'
        ELSE 'cancelled'
    END
FROM generate_series(1, 2000) i
ON CONFLICT DO NOTHING;
EOF

# Update table statistics for better query planning
echo "📈 Updating table statistics..."
psql -U "$USER" -h "$HOST" -p "$PORT" -d "$DBNAME" -c "ANALYZE;"

# Display setup summary
echo ""
echo "✅ QueryIQ Database Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️ Database: $DBNAME"
echo "👤 User: $USER" 
echo "🌐 Host: $HOST:$PORT"
echo ""
echo "📊 Created Tables:"
echo "  • query_logs (for SQL query tracking)"
echo "  • execution_plans (for EXPLAIN plan analysis)"  
echo "  • query_features (for ML feature extraction)"
echo "  • suggestions (for optimization recommendations)"
echo "  • performance_improvements (for benchmark results)"
echo ""
echo "🎯 Sample Data:"
echo "  • 1,000 users"
echo "  • 500 products across 5 categories" 
echo "  • 2,000 orders"
echo ""
echo "🚀 Next Steps:"
echo "  1. Set your GEMINI_API_KEY in .env file"
echo "  2. Run: python scripts/demo.py --full"
echo "  3. Start app: python app/main.py"
echo "  4. Visit: http://localhost:8000/dashboard.html"
echo ""
echo "Happy optimizing! 🎉"