#!/bin/bash

echo "🚀 Starting Markaba Backend..."

# Debug environment variables
echo "📄 Environment variables starting with 'aiven':"
env | grep -i aiven | head -10

# Write SSL certificate content to file if environment variable exists
# Check for the SSL certificate content environment variable
CERT_VAR_NAME="aiven-pg-sslrootcert-content"
CERT_CONTENT=$(printenv "$CERT_VAR_NAME")

if [ ! -z "$CERT_CONTENT" ]; then
    echo "✅ Found SSL cert content in $CERT_VAR_NAME"
    echo "✅ Writing SSL certificate to /app/ca.pem"
    echo -e "$CERT_CONTENT" > /app/ca.pem
    chmod 600 /app/ca.pem
    echo "📊 Certificate file size: $(ls -l /app/ca.pem)"
    echo "📄 First few characters of cert: $(head -c 50 /app/ca.pem)"
else
    echo "❌ SSL certificate content not found in environment variables"
    echo "Looking for variables containing 'cert' or 'ssl':"
    env | grep -i -E "(cert|ssl)" | head -5
fi

echo "🌟 Starting the application..."
exec python run.py
