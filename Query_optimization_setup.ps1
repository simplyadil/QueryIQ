# Define the path to the config.json file
$configPath = "config.json"

# Load the config.json file
$config = Get-Content -Path $configPath | ConvertFrom-Json

# Define PostgreSQL paths
$PG_VERSION = "17"  # Change if using a different version
$PG_CONF = "C:\Program Files\PostgreSQL\$PG_VERSION\data\postgresql.conf"
$PG_SERVICE = "postgresql-x64-$PG_VERSION"

Write-Host "🚀 Starting PostgreSQL Optimization Setup for $pgDbName DB..." -ForegroundColor Green

# Step 1: Enable pg_stat_statements in postgresql.conf
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

# Step 3: Connect to PostgreSQL and set up the lego database using config.json values
Write-Host "📡 Connecting to $pgDbName DB..."
$psqlCommand = "C:\Program Files\PostgreSQL\$PG_VERSION\bin\psql.exe"
$pgUser = $config.user
$pgPassword = $config.password
$pgHost = $config.host
$pgPort = $config.port
$pgDbName = $config.dbname

$env:PGPASSWORD = $pgPassword

# Create the pg_stat_statements extension in the lego database
& $psqlCommand -U $pgUser -d $pgDbName -h $pgHost -p $pgPort -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
Write-Host "✅ pg_stat_statements extension enabled in $pgDbName DB."

# Step 4: Create the query_performance_log table in the lego database
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
    log_time TIMESTAMP DEFAULT NOW()
);
"@
& $psqlCommand -U $pgUser -d $pgDbName -h $pgHost -p $pgPort -c $createTableSQL
Write-Host "✅ query_performance_log table created in $pgDbName DB."

# Step 5: Insert initial query data from pg_stat_statements into query_performance_log
$insertCommand = @"
INSERT INTO query_performance_log (query, calls, total_exec_time, mean_exec_time, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written)
SELECT query, calls, total_exec_time, mean_exec_time, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written
FROM pg_stat_statements
ON CONFLICT DO NOTHING;
"@
& $psqlCommand -U $pgUser -d $pgDbName -h $pgHost -p $pgPort -c "$($insertCommand)"
Write-Host "✅ Initial query data logged in $pgDbName DB."

Write-Host "🎉 Setup Complete! $pgDbName DB is now collecting query performance data." -ForegroundColor Green
