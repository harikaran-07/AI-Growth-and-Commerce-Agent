@echo off
echo Starting MerchantFlow AI...

echo.
echo [1/3] Setting up backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
python seed.py
echo Backend setup complete!

echo.
echo [2/3] Setting up frontend...
cd ..\frontend
call npm install --silent
echo Frontend setup complete!

echo.
echo [3/3] Starting servers...
echo Starting backend on http://localhost:8000
start cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:3000
start cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo MerchantFlow AI is starting!
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
pause
