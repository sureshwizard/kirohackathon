@echo off
echo 🌍 Starting Monexa Demo...
echo.

echo 📊 Setting up demo data...
python demo_setup.py

echo.
echo 🚀 Starting backend server...
echo Backend will be available at http://localhost:8000
start cmd /k "cd backend_expenses && python -m uvicorn app:app --reload --port 8000"

echo.
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo 🎨 Starting frontend server...
echo Frontend will be available at http://localhost:3000
start cmd /k "cd frontend && npm start"

echo.
echo ✅ Monexa is starting up!
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause > nul