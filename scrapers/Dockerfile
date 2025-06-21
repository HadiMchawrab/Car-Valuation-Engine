FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the scraper code
COPY . .

# Create a directory for output data
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Define the default command to run when the container starts
CMD ["scrapy", "crawl", "dubizzle"]
