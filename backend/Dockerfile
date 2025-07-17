FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Ensure ca.pem exists and has proper permissions (it will be created by run.py)
RUN touch /app/ca.pem && chmod 600 /app/ca.pem

EXPOSE 8000

CMD ["python", "run.py"]
