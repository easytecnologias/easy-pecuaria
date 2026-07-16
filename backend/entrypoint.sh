#!/bin/sh
set -e

# aplica migrations (no-op se ja estiver no head)
alembic upgrade head

# sobe a API
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
