# Load configuration
$configPath = "config.json"
if (-not (Test-Path $configPath)) {
    Write-Error "Configuration file not found: $configPath"
    exit 1
}

$config = Get-Content $configPath | ConvertFrom-Json

# Set PostgreSQL paths
$PG_VERSION = "17"
$psqlCommand = "C:\Program Files\PostgreSQL\$PG_VERSION\bin\psql.exe"

# Set password for psql
$env:PGPASSWORD = $config.password

Write-Host "🚀 Starting PostgreSQL Optimization Setup for $($config.dbname) DB..."

# Create database if it doesn't exist
& $psqlCommand -U $config.user -h $config.host -d "postgres" -c "CREATE DATABASE $($config.dbname);"

# Create pg_stat_statements extension
& $psqlCommand -U $config.user -d $config.dbname -h $config.host -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

# Create query_performance_log table
$createTableQuery = @"
CREATE TABLE IF NOT EXISTS query_performance_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query TEXT,
    calls INTEGER,
    total_exec_time FLOAT,
    mean_exec_time FLOAT,
    shared_blks_hit INTEGER,
    shared_blks_read INTEGER,
    temp_blks_read INTEGER,
    temp_blks_written INTEGER,
    query_length INTEGER,
    num_select INTEGER,
    num_from INTEGER,
    num_where INTEGER,
    num_join INTEGER,
    num_group_by INTEGER,
    num_order_by INTEGER,
    num_distinct INTEGER,
    num_limit INTEGER,
    query_complexity INTEGER
);
"@

& $psqlCommand -U $config.user -d $config.dbname -h $config.host -c $createTableQuery

# Create sample tables for testing
$createSampleTablesQuery = @"
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    age INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10,2),
    stock INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (name, email, age, status)
SELECT 
    'User ' || i,
    'user' || i || '@example.com',
    20 + (i % 50),
    CASE WHEN i % 3 = 0 THEN 'active' ELSE 'inactive' END
FROM generate_series(1, 100) i
ON CONFLICT DO NOTHING;

INSERT INTO products (name, category, price, stock)
SELECT 
    'Product ' || i,
    CASE 
        WHEN i % 3 = 0 THEN 'electronics'
        WHEN i % 3 = 1 THEN 'clothing'
        ELSE 'books'
    END,
    10.99 + (i % 100),
    100 + (i % 900)
FROM generate_series(1, 50) i
ON CONFLICT DO NOTHING;

INSERT INTO orders (user_id, amount, status)
SELECT 
    1 + (i % 100),
    99.99 + (i % 900),
    CASE 
        WHEN i % 4 = 0 THEN 'completed'
        WHEN i % 4 = 1 THEN 'pending'
        WHEN i % 4 = 2 THEN 'processing'
        ELSE 'cancelled'
    END
FROM generate_series(1, 200) i
ON CONFLICT DO NOTHING;
"@

& $psqlCommand -U $config.user -d $config.dbname -h $config.host -c $createSampleTablesQuery

Write-Host "✅ Setup complete!" 