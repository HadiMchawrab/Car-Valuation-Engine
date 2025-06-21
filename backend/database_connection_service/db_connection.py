import os
import mysql.connector
import time
from mysql.connector import Error

def get_connection():
    # Maximum number of retry attempts
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Get environment variables with default values if not set
            host = os.getenv("DATABASE_HOST", "database")
            port = int(os.getenv("DATABASE_PORT", "3306"))
            user = os.getenv("DATABASE_USER", "root")
            password = os.getenv("DATABASE_PASSWORD", "123")
            database = os.getenv("DATABASE_NAME", "Markaba_trial")
            
            print(f"Attempting to connect to database: host={host}, port={port}, database={database}")
            
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            
            if connection.is_connected():
                print(f"Successfully connected to MySQL database (Attempt {attempt+1})")
                return connection
            
        except Error as e:
            print(f"Error while connecting to MySQL (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Increase the delay for the next attempt (exponential backoff)
                retry_delay *= 2
    
    print("Failed to connect to MySQL after multiple attempts")
    return None
