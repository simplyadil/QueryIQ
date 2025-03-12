# Define PostgreSQL paths (change version if necessary)
$PG_VERSION = "17"  # Change if using a different version
$PG_CONF = "C:\Program Files\PostgreSQL\$PG_VERSION\data\postgresql.conf"
$PG_SERVICE = "postgresql-x64-$PG_VERSION"

Write-Host "🚀 Starting PostgreSQL Optimization Setup..." -ForegroundColor Green

if (Select-String "shared_preload_libraries" $PG_CONF) {
    
    Write-Host "✅ pg_stat_statements is already enabled."
} else {
    Write-Host "🔧 Enabling pg_stat_statements..."
    Add-Content $PG_CONF "`nshared_preload_libraries = 'pg_stat_statements'"
    Add-Content $PG_CONF "`npg_stat_statements.track = all"

    # Step 2: Restart PostgreSQL to apply changes
    Write-Host "🔄 Restarting PostgreSQL service..."
    Restart-Service -Name $PG_SERVICE -Force
    Start-Sleep -Seconds 5
}




# Step 3: Connect to PostgreSQL and create required extension & table
Write-Host "📡 Connecting to PostgreSQL..."
$psqlCommand = "C:\Program Files\PostgreSQL\$PG_VERSION\bin\psql.exe"
$pgUser = "postgres"  # Change if using a different user
$pgPassword = "Dbsop100"  # Change to match your password
$env:PGPASSWORD = $pgPassword  # Set password for authentication

# Run SQL commands
& $psqlCommand -U $pgUser -d postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
Write-Host "✅ pg_stat_statements extension enabled."

$createTableSQL = @"
CREATE TABLE IF NOT EXISTS query_performance_log (
    id SERIAL PRIMARY KEY,
    query TEXT,
    calls INTEGER,
    total_exec_time DOUBLE PRECISION,
    mean_exec_time DOUBLE PRECISION,
    shared_blks_hit BIGINT,
    shared_blks_read BIGINT,
    temp_blks_read BIGINT,
    temp_blks_written BIGINT,
    optimized_query TEXT DEFAULT NULL,
    improvement_percentage DOUBLE PRECISION DEFAULT NULL,
    log_time TIMESTAMP DEFAULT NOW()
);
"@
& $psqlCommand -U $pgUser -d postgres -c $createTableSQL

Write-Host "✅ query_performance_log table created."

# Step 4: Insert initial query data
$insertcommand = @"
INSERT INTO query_performance_log (query, calls, total_exec_time, mean_exec_time, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written)
SELECT query, calls, total_exec_time, mean_exec_time, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written 
FROM pg_stat_statements ON CONFLICT DO NOTHING;
"@

& $psqlCommand -U $pgUser -d postgres -c $insertcommand

Write-Host "✅ Initial query data logged."

Write-Host "🎉 Setup Complete! PostgreSQL is now collecting query performance data." -ForegroundColor Green
