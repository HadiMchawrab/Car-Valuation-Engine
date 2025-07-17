import os
import time
import psycopg2
from psycopg2 import OperationalError
import logging

logger = logging.getLogger(__name__)

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
            
            # Log connection attempt (without sensitive data)
            logger.info(f"Attempt {attempt}: Connecting to {host}:{port}/{dbname} as {user}")
            logger.info(f"SSL cert path: {sslrootcert}")
            
            # Check if SSL certificate file exists
            if sslrootcert and not os.path.exists(sslrootcert):
                logger.error(f"SSL certificate file not found at: {sslrootcert}")
                raise OperationalError(f"SSL certificate file not found: {sslrootcert}")
            
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
            
            logger.info("Database connection successful!")
            return conn

        except OperationalError as e:
            logger.error(f"Database connection attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All database connection attempts failed")

    return None
