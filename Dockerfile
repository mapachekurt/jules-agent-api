FROM python:3.11-slim

WORKDIR /app

# Install git and create data directory
RUN apt-get update && apt-get install -y git && apt-get clean
RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
