# Monexa Project Structure

## Root Directory
```
monexa/
├── backend_expenses/          # Main backend API server
├── backend_ingest/           # Data ingestion service
├── frontend/                 # React frontend application
├── data/                     # Database and sample data files
├── sample-data/              # Additional test data
├── docs/                     # Documentation (empty)
├── .env                      # Environment configuration
├── .env.example              # Environment template
├── README.md                 # Main project documentation
├── SUBMISSION.md             # Hackathon submission details
├── PROJECT_STRUCTURE.md      # This file
├── demo_setup.py             # Demo data setup script
├── start_demo.bat            # Windows quick start script
└── normalize_existing_db.py  # Database normalization utility
```

## Backend Expenses (`backend_expenses/`)
Main FastAPI application handling expenses, reports, and chat functionality.

**Key Files:**
- `app.py` - Main FastAPI application
- `models.py` - SQLAlchemy database models
- `crud.py` - Database operations
- `chat.py` - AI chat assistant
- `database.py` - Database configuration
- `requirements.txt` - Python dependencies

## Backend Ingest (`backend_ingest/`)
Specialized service for parsing and ingesting financial data from various sources.

**Key Files:**
- `app.py` - Ingest API server
- `parsers/` - Data parsers for different sources
- `dedupe.py` - Duplicate detection logic

## Frontend (`frontend/`)
React application with TypeScript, providing the user interface.

**Key Files:**
- `src/` - Source code
- `package.json` - Node.js dependencies
- `vite.config.ts` - Vite configuration
- `tsconfig.json` - TypeScript configuration

## Data (`data/`)
Contains the SQLite database and sample CSV files for testing.

**Files:**
- `finance.db` - Main SQLite database
- `*.csv` - Sample data files for different sources

## Quick Start
1. Run `python demo_setup.py` to initialize demo data
2. Use `start_demo.bat` on Windows for automated startup
3. Or manually start backend and frontend servers as per README

## Architecture Highlights
- **Microservices**: Separate ingest and expenses services
- **Database**: SQLite with SQLAlchemy ORM
- **API**: RESTful FastAPI with automatic documentation
- **Frontend**: Modern React with TypeScript and Vite
- **AI Integration**: OpenAI GPT with rule-based fallback
- **Data Processing**: Flexible parser system for multiple sources