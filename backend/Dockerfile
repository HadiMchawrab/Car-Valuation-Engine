FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Make startup script and run.py executable
RUN chmod +x startup.sh run.py

CMD ["./startup.sh"]
