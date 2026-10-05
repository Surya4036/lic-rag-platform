FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app/ ./app/
COPY data/ ./data/
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 8000 8080 8501

ENV PORT=8080
CMD ["/bin/bash", "./start.sh"]
