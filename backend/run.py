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
    else:
        print("ℹ️ No SSL cert content found in environment variables")
    
    print("🌟 Starting the application...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
