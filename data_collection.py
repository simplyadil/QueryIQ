import psycopg2
import time
import csv
import json
from datetime import datetime

config_file_path = 'config.json'

with open(config_file_path, 'r') as f:
    db_config = json.load(f)

extract_sql = """
SELECT query, calls, total_exec_time, mean_exec_time, 
       shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written
FROM pg_stat_statements
ORDER BY total_exec_time DESC;
"""

# CSV file to store training data
csv_filename = "training_data.csv"

def collect_data():
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(extract_sql)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error collecting data from lego DB: {e}")
        return []

def write_to_csv(rows):
    # Check if CSV file already exists; if not, we'll write a header
    try:
        with open(csv_filename, 'r', newline='') as csvfile:
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow([
                "query", "calls", "total_exec_time", "mean_exec_time", 
                "shared_blks_hit", "shared_blks_read", 
                "temp_blks_read", "temp_blks_written", "log_time"
            ])
        log_time = datetime.now().isoformat()
        for row in rows:
            writer.writerow(list(row) + [log_time])
    print(f"[{log_time}] Wrote {len(rows)} records to {csv_filename}.")

if __name__ == "__main__":
    while True:
        print("Collecting data from lego DB...")
        rows = collect_data()
        if rows:
            write_to_csv(rows)
        else:
            print("No data returned from lego DB.")
        time.sleep(60)
