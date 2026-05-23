@echo off
echo Starting Gold Tracker Application...

echo.
echo Starting Backend Server (FastAPI)...
start "Gold Tracker Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"

echo.
echo Starting Frontend Server (Next.js)...
start "Gold Tracker Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting in separate windows.
echo - Backend API will be available at: http://localhost:8000
echo - Frontend UI will be available at: http://localhost:3000
echo.
echo Close this window or press any key to exit the launcher.
pause >nul
