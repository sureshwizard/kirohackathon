🌍 Monexa — The Future of Personal \& Household Finance AI



Hackathon Vision:

Imagine a world where every individual, in any country, can instantly understand their spending, spot waste, and plan better — without needing spreadsheets, financial expertise, or hours of manual tracking.

Monexa is built for that world. It’s a universal Expense Intelligence Platform powered by AI, open parsers, and a human-friendly dashboard.



🏗 System Architecture

High-Level Flow

                 ┌─────────────┐

   CSV / Bill →  │   Parsers   |    │  (Amazon, Banks, GPay, Paytm, PhonePe, Generic…)

                 └──────┬──────┘

                        │

                        ▼

                 ┌─────────────┐

                 │   Backend   |     │      (FastAPI)

                 │  Ingest API |     │

                 └──────┬──────┘

                        │

                        ▼

                ┌─────────────────┐

                │    Database     |     │ (SQLite / SQLAlchemy)

                │ expenses + items|     │

                └──────┬──────────┘

                          │

          ┌────────────┼────────────────────────┐

          ▼              ▼                           ▼

   ┌────────────┐ ┌────────────┐ ┌───────────────┐

   │ Dashboard  │ │ Reports UI │ │ Chat Assistant│

   │ (Charts)   │ │ Compare Mth│ │ (Text/Voice)  │

   └────────────┘ └────────────┘ └───────────────┘



Chat Assistant Flow

 User Question

     │

     ▼

┌───────────────┐

│ Chat Endpoint │

└──────┬────────┘

         │

   ┌───▼─────────────┐

   │ Rule-based NLP  │  ("how much spent", "top merchants", "by category")

   └───┬─────────────┘

         │ fallback if use\_ai = true

         ▼

   ┌───────────────┐

   │ OpenAI (LLM)  │

   └───────────────┘

          │

          ▼

   ┌───────────────┐

   │ JSON Response │

   └───────────────┘

          │

          ▼

  UI (text + speech)



✅ Current Hackathon Build



Backend (FastAPI + SQLite):

Expense storage (expenses, expense\_items)

Import pipeline with parsers for multiple sources

Reports API (monthly totals, category comparison)

Chat API with rule-based + AI mode



Frontend (React + Recharts):

Dashboard with totals, averages, bar/pie/line charts

Import screen for CSVs

Reports (month vs. month comparison)

Chat UI with speech input + TTS output



Data Model:

expenses (header: date, type, amount, note, source, txn\_id)

expense\_items (details: qty, amount — supports itemized bills)



AI Integration Ready:

Switch use\_ai = true to enable OpenAI responses

Chat assistant can be extended with full LLM context (project docs + DB)



🛤 Roadmap



Universal Ingest (Q4 2025)

More parsers: PayPal, Stripe, Razorpay, WeChat Pay, Apple Pay

OCR for paper bills \& receipts



AI Summaries (2026)

“Explain my spending in 3 sentences”

“Suggest how to save 20%”



IoT \& Real-Time Sync (2026)

Smart fridge auto-log groceries

NFC wallets for micro-payments



Global Scalability (2027)

Multi-currency, crypto wallets

Developer plugin marketplace



Financial Inclusion (2027)

Voice-first rural support

Offline-first small devices

NGO/Gov use for subsidies



⚙️ Setup \& Run

\#.env must contains the following 

\# Backend config

FINANCE\_DB=yourpath to data/finance.db

EXPENSES\_PORT=8000

INGEST\_PORT=8001



\# If using OpenAI (only if mandatory for hackathon)

OPENAI\_API\_KEY=<youropenaikey>

\# Clone

git clone https://github.com/sureshwizard/kirohackathon.git

cd kirohackathon



\# Backend

cd backend\_expenses

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn backend\_expenses.app:app --reload --port 8000



\# Frontend

cd frontend

npm install

npm start





Open: http://localhost:3000



🎤 Sample Chat Prompts



“How much I spent on coffee this month?”

“Show expenses by category this month.”

“Top 5 merchants I spent with this month.”

“List transactions above 1000 rupees this month.”



🏆 Why This Project Wins



Universality — works across banks, wallets, receipts worldwide

Accessibility — natural language + speech

Impact — empowers families, students, NGOs, small businesses

Scalability — AI, IoT, multi-currency roadmap



Monexa isn’t just a hackathon app.

It’s a blueprint for the future of personal finance management worldwide.



✨ Built to help the world see where their money flows — and choose better routes.



📊 Example Data (for Import \& Testing)



Copy any of these into a CSV file and import via Frontend → Import → Generic/Source.

The system will auto-detect the parser from source.



🛒 Generic Groceries

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-01,groceries,1500.00,Supermarket Bill,generic,GEN-001

2025-09-02,groceries,220.00,Tomatoes 2kg,generic,GEN-002

2025-09-02,groceries,800.00,Rice 10kg,generic,GEN-003



💳 GPay

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-03,gpay,450.00,Big Bazaar,gpay,GPAY-001

2025-09-03,gpay,60.50,Auto Driver,gpay,GPAY-002

2025-09-04,gpay,-1200.00,Movie Theatre Refund,gpay,GPAY-003



🏦 Bank (India)

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-05,misc,5000.00,Salary Credit,Bank\_India,BANKIN-001

2025-09-06,misc,-1200.00,ATM Withdrawal,Bank\_India,BANKIN-002

2025-09-07,utilities,-800.00,Electricity Bill,Bank\_India,BANKIN-003



🏦 Bank (USA)

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-08,misc,3000.00,Salary Credit,Bank\_USA,BANKUS-001

2025-09-09,shopping,-150.00,Amazon Purchase,Bank\_USA,BANKUS-002

2025-09-09,transport,-50.00,Uber Ride,Bank\_USA,BANKUS-003



🛍 Amazon

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-10,shopping,999.00,Wireless Headphones,amazon,AMZ-001

2025-09-10,shopping,450.00,Books,amazon,AMZ-002



📱 Paytm

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-11,food,300.00,Swiggy Order,paytm,PAYTM-001

2025-09-12,transport,120.00,Metro Ticket,paytm,PAYTM-002



📱 PhonePe

tx\_datetime,exp\_type,total\_amount,note,source,txn\_id

2025-09-13,groceries,850.00,Local Kirana,phonepe,PHNPE-001

2025-09-14,utilities,600.00,Gas Bill,phonepe,PHNPE-002

