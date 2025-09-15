# Monexa - Kiro Hackathon Submission

## Project Overview
Monexa is a universal Expense Intelligence Platform powered by AI that helps individuals understand their spending, spot waste, and plan better without needing spreadsheets or financial expertise.

## Key Features
- **Universal Data Import**: Supports multiple sources (Amazon, Banks, GPay, Paytm, PhonePe, Generic CSV)
- **AI-Powered Chat Assistant**: Natural language queries with speech input/output
- **Interactive Dashboard**: Charts, reports, and month-to-month comparisons
- **Real-time Analytics**: Spending patterns, category analysis, merchant insights
- **Multi-platform Support**: Works across different payment systems globally

## Technical Stack
- **Backend**: FastAPI, SQLite, SQLAlchemy
- **Frontend**: React, TypeScript, Vite, Recharts
- **AI**: OpenAI GPT integration with fallback rule-based NLP
- **Data Processing**: Custom parsers for different financial data formats

## Innovation Highlights
1. **Universal Compatibility**: Works with any financial data source
2. **Accessibility First**: Voice input/output for inclusive design
3. **Scalable Architecture**: Ready for IoT, multi-currency, and global expansion
4. **Real-world Impact**: Empowers families, students, NGOs, and small businesses

## Demo Instructions
1. Clone the repository
2. Set up environment variables in `.env`
3. Run backend: `cd backend_expenses && uvicorn app:app --reload --port 8000`
4. Run frontend: `cd frontend && npm install && npm start`
5. Access at http://localhost:3000

## Sample Queries
- "How much I spent on coffee this month?"
- "Show expenses by category this month"
- "Top 5 merchants I spent with this month"
- "List transactions above 1000 rupees this month"

## Future Vision
Monexa isn't just a hackathon app - it's a blueprint for democratizing financial intelligence worldwide, with plans for IoT integration, multi-currency support, and financial inclusion initiatives.

## Built with ❤️ for the Kiro Hackathon