#!/bin/sh
set -eu
python -m alembic upgrade head
python -m app.seed.seed_trails
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 --timeout 120
