import os
import time
import psycopg2
from psycopg2 import OperationalError

def get_connection():
    max_retries = 5
    retry_delay = 2  # seconds
    
    # env-var keys
    host_key       = "aiven-pg-host"
    port_key       = "aiven-pg-port"
    db_key         = "aiven-pg-db"
    user_key       = "aiven-pg-user"
    password_key   = "aiven-pg-password"
    sslcert_key    = "aiven-pg-sslrootcert"
    
    for attempt in range(1, max_retries+1):
        try:
            host       = os.getenv(host_key)
            port       = int(os.getenv(port_key, 5432))
            dbname     = os.getenv(db_key)
            user       = os.getenv(user_key)
            password   = os.getenv(password_key)
            sslrootcert= os.getenv(sslcert_key)
            
            print(f"Attempting to connect to Postgres: host={host}, port={port}, db={dbname}")
            
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                sslmode="verify-ca",
                sslrootcert=sslrootcert
            )
            conn.autocommit = True
            
            print(f"✓ Connected to Postgres (Attempt {attempt})")
            return conn

        except OperationalError as e:
            print(f"✗ Connection failed (Attempt {attempt}): {e}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay}s…")
                time.sleep(retry_delay)
                retry_delay *= 2

    print("⚠️  Failed to connect after multiple attempts")
    return None
