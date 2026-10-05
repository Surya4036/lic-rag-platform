#!/bin/bash
set -e

# Start FastAPI in background on port 8000
echo "Starting FastAPI backend server..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Set FastAPI URL for Streamlit
export FASTAPI_API_URL="http://127.0.0.1:8000"

# Start Streamlit UI on ${PORT:-8080}
echo "Starting Streamlit UI on port ${PORT:-8080}..."
exec streamlit run app/ui.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
