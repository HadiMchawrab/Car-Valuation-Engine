import uvicorn
import os

if __name__ == "__main__":
    print("🚀 Starting Markaba Backend...")
    
    # Handle SSL certificate if provided as environment variable
    cert_content = os.environ.get("aiven-pg-sslrootcert-content")
    if cert_content:
        print("✅ Writing SSL certificate to /app/ca.pem")
        with open("/app/ca.pem", "w") as f:
            f.write(cert_content)
        os.chmod("/app/ca.pem", 0o600)
        # Set the environment variable to point to the written certificate
        os.environ["aiven-pg-sslrootcert"] = "/app/ca.pem"
    else:
        print("ℹ️ No SSL cert content found in environment variables")
    
    # Debug: Print environment variables (without sensitive data)
    print(f"🔍 Database host: {os.environ.get('aiven-pg-host', 'NOT SET')}")
    print(f"🔍 Database port: {os.environ.get('aiven-pg-port', 'NOT SET')}")
    print(f"🔍 Database name: {os.environ.get('aiven-pg-db', 'NOT SET')}")
    print(f"🔍 Database user: {os.environ.get('aiven-pg-user', 'NOT SET')}")
    print(f"🔍 SSL cert path: {os.environ.get('aiven-pg-sslrootcert', 'NOT SET')}")
    
    print("🌟 Starting the application...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)