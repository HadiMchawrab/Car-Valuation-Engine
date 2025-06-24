FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make sure run.py is executable
RUN chmod +x run.py

CMD ["python", "run.py"]
