import re
import psycopg2
import time
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
import os


## log file 
LOG_FILE = "/var/log/nginx/access.log"  
ERROR_PATTERN = re.compile(r'(\d{3})\s.*CN=([a-zA-Z0-9.-]+)')

# Database connectiong 
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": 5432,
}


# SQL Tables
CREATE_TABLE_HTTP = """
CREATE TABLE IF NOT EXISTS http_status_counts (
    id SERIAL PRIMARY KEY,
    status_code INT NOT NULL,
    count INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
# SQL Tables
CREATE_TABLE_CN = """
CREATE TABLE IF NOT EXISTS cn_counts (
    id SERIAL PRIMARY KEY,
    cn TEXT NOT NULL,
    count INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Extract HTTP  codes from log file
def parse_http_statuses(log_file):
    status_pattern = re.compile(r'\s(\d{3})\s')  # Captures 3-digit HTTP codes
    counter = Counter()

    with open(log_file, "r") as file:
        for line in file:
            match = status_pattern.search(line)
            if match:
                status_code = match.group(1)
                counter[status_code] += 1

    return counter

# Extract CNs from logs
CN_PATTERN = re.compile(r'CN=([a-zA-Z0-9.-]+)')

def parse_bad_cns(log_file):
    counter = Counter()

    # with open(log_file, "r") as file:
    #     for line in file:
    #         match = CN_PATTERN.search(line)
    #         if match:
    #             cn = match.group(1)
    #             counter[cn] += 1

    with open(log_file, "r") as file:
        for line in file:
            match = ERROR_PATTERN.search(line)
            if match:
                status_code = match.group(1)
                cn = match.group(2)
                
                if status_code == "400":  # Only interested in 400 error codes
                    counter[cn] += 1

    return counter

# Insert data into PostgreSQL
def insert_into_db(status_counts, cn_counts):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Creating if table does not exist
    cur.execute(CREATE_TABLE_HTTP)
    cur.execute(CREATE_TABLE_CN)

    # Insert to db 
    for status, count in status_counts.items():
        cur.execute(
            "INSERT INTO http_status_counts (status_code, count, timestamp) VALUES (%s, %s, %s);",
            (status, count, datetime.now()),
        )

    # Insert to db 
    for cn, count in cn_counts.items():
        cur.execute(
            "INSERT INTO cn_counts (cn, count, timestamp) VALUES (%s, %s, %s);",
            (cn, count, datetime.now()),
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Data inserted at {datetime.now()}")

# Run CMD
if __name__ == "__main__":
    while True:
        http_counts = parse_http_statuses(LOG_FILE)
        cn_counts = parse_bad_cns(LOG_FILE)

        if http_counts or cn_counts:
            insert_into_db(http_counts, cn_counts)
        else:
            print(f"⚠️ No new data found at {datetime.now()}")

        time.sleep(120)  # Sleep for 2 minutes (120 seconds)