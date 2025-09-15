# Technology Stack

## Backend
- **Framework**: FastAPI with Python 3.x
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: OpenAI GPT API with rule-based fallback
- **Server**: Uvicorn ASGI server
- **Architecture**: Microservices (separate ingest and expenses services)

## Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Charts**: Recharts and Chart.js
- **HTTP Client**: Axios
- **Routing**: React Router DOM

## Key Dependencies
- **Backend**: fastapi, sqlalchemy, openai, python-dotenv, uvicorn
- **Frontend**: react, typescript, recharts, axios, react-router-dom

## Common Commands

### Initial Setup
```bash
# Setup demo data
python demo_setup.py

# Quick start (Windows)
start_demo.bat
```

### Backend Development
```bash
cd backend_expenses
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Development server
npm run build  # Production build
```

### Environment Configuration
- Copy `.env.example` to `.env`
- Set `FINANCE_DB` path to database location
- Configure `OPENAI_API_KEY` for AI features
- Set ports: `EXPENSES_PORT=8000`, `INGEST_PORT=8001`

## API Documentation
- Backend API docs available at `http://localhost:8000/docs`
- Automatic OpenAPI/Swagger documentation via FastAPI