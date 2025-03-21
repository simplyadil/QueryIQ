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

# Expected header
expected_header = [
    "query", "calls", "total_exec_time", "mean_exec_time", 
    "shared_blks_hit", "shared_blks_read", 
    "temp_blks_read", "temp_blks_written", "log_time"
]

def check_and_correct_header():
    """
    Check if the CSV file exists and if its header matches the expected header.
    If not, rewrite the file with the correct header, preserving the old data.
    """
    try:
        with open(csv_filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            existing_header = next(reader, None)
            # If header is missing or does not match, rewrite file with correct header
            if existing_header != expected_header:
                print("Header is incorrect or missing. Rewriting file with correct header.")
                # Read all existing data (skip header if it exists)
                data = list(reader)
                # Open file in write mode and write correct header, then old data
                with open(csv_filename, 'w', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(expected_header)
                    for row in data:
                        writer.writerow(row)
            else:
                print("CSV header is correct.")
    except FileNotFoundError:
        # File doesn't exist; nothing to check
        print("CSV file does not exist yet.")

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
    # First, check and correct header if necessary
    check_and_correct_header()
    
    # Open the CSV file in append mode
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
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
