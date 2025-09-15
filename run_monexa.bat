@echo off
REM === Monexa Project Launcher ===

REM Backend - Expenses API
start "Monexa - Expenses API (8000)" cmd /k ^
"cd /d C:\BUSINESS\21-Projects\monexa && ^
call .venv\Scripts\activate && ^
python -m uvicorn backend_expenses.app:app --host 0.0.0.0 --port 8000 --reload"

REM Backend - Ingest API
start "Monexa - Ingest API (8001)" cmd /k ^
"cd /d C:\BUSINESS\21-Projects\monexa && ^
call .venv\Scripts\activate && ^
python -m uvicorn backend_ingest.app:app --host 0.0.0.0 --port 8001 --reload"

REM Frontend - React UI
start "Monexa - Frontend (3000)" cmd /k ^
"cd /d C:\BUSINESS\21-Projects\monexa\frontend && ^
call npm start"

REM Optional message
echo Launched Monexa: Expenses API (8000), Ingest API (8001), and Frontend (3000).
