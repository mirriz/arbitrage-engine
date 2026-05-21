@echo off
echo Booting up the Arbitrage Engine...

:: 1. Start Database and Redis in the background
echo Starting Docker containers...
docker-compose up -d

:: 2. Start FastAPI Backend
echo Starting FastAPI...
start "FastAPI Backend" cmd /k "call .venv\Scripts\activate && cd backend && uvicorn app.main:app --reload"

:: 3. Start Celery Worker
echo Starting Celery Worker...
start "Celery Worker" cmd /k "call .venv\Scripts\activate && cd backend && celery -A app.worker.celery_app.celery_app worker --loglevel=info --pool=solo"

:: 4. Start Next.js Frontend
echo Starting Next.js...
start "Next.js Frontend" cmd /k "cd frontend && npm run dev"

echo All systems are launching! You can close this main window.