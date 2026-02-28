#!/usr/bin/env bash
set -e

# Run FastAPI in background (internal)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 &

# Run Streamlit (public port for HF)
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 7860
