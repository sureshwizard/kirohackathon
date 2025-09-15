# Project Structure & Organization

## Root Directory Layout
```
monexa/
├── backend_expenses/     # Main FastAPI expenses API
├── backend_ingest/      # Data ingestion microservice  
├── frontend/            # React TypeScript UI
├── data/               # SQLite database & sample CSVs
├── sample-data/        # Test data for different sources
├── .env                # Environment configuration
└── demo_setup.py       # Demo data initialization
```

## Backend Architecture

### Main Backend (`backend_expenses/`)
- **`app.py`** - FastAPI application entry point
- **`models.py`** - SQLAlchemy models and Pydantic schemas
- **`crud.py`** - Database operations and queries
- **`chat.py`** - AI chat assistant logic
- **`database.py`** - Database connection and session management
- **`utils.py`** - Utility functions and helpers

### Ingest Service (`backend_ingest/`)
- **`app.py`** - Separate FastAPI service for data ingestion
- **`parsers/`** - Source-specific data parsers (Amazon, GPay, banks, etc.)
- **`dedupe.py`** - Duplicate transaction detection

## Frontend Structure (`frontend/`)
- **`src/`** - React TypeScript source code
- **`public/`** - Static assets
- **`package.json`** - Dependencies and scripts
- **`vite.config.ts`** - Build configuration

## Data Model
- **`expenses`** table: Main transaction records (date, type, amount, source, txn_id)
- **`expense_items`** table: Itemized details for receipts/bills
- Supports both simple transactions and detailed itemized expenses

## Naming Conventions
- **Files**: snake_case for Python, camelCase for TypeScript
- **Database**: snake_case table and column names
- **API endpoints**: RESTful with clear resource naming
- **Transaction IDs**: Source-prefixed (e.g., GPAY-001, AMZ-002)

## Key Patterns
- **Microservices**: Separate concerns (expenses vs ingestion)
- **ORM**: SQLAlchemy for database abstraction
- **Type Safety**: Pydantic schemas for API validation
- **CORS**: Enabled for frontend-backend communication
- **Environment**: `.env` for configuration management