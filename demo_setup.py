#!/usr/bin/env python3
"""
Monexa Demo Setup Script
Prepares the database with sample data for demonstration
"""

import sqlite3
import os
from datetime import datetime, timedelta

def setup_demo_data():
    """Setup demo data for Monexa presentation"""
    
    # Database path
    db_path = "data/finance.db"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_datetime TEXT NOT NULL,
            exp_type TEXT NOT NULL,
            total_amount REAL NOT NULL,
            note TEXT,
            source TEXT NOT NULL,
            txn_id TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (expense_id) REFERENCES expenses (id)
        )
    ''')
    
    # Sample demo data
    demo_expenses = [
        ('2025-09-01 10:30:00', 'groceries', 1500.00, 'Weekly Grocery Shopping', 'generic', 'DEMO-001'),
        ('2025-09-02 14:15:00', 'food', 450.00, 'Lunch at Restaurant', 'gpay', 'DEMO-002'),
        ('2025-09-03 09:20:00', 'transport', 120.00, 'Metro Card Recharge', 'paytm', 'DEMO-003'),
        ('2025-09-04 16:45:00', 'shopping', 999.00, 'Wireless Headphones', 'amazon', 'DEMO-004'),
        ('2025-09-05 11:30:00', 'utilities', 800.00, 'Electricity Bill', 'phonepe', 'DEMO-005'),
        ('2025-09-06 19:20:00', 'food', 300.00, 'Dinner Delivery', 'gpay', 'DEMO-006'),
        ('2025-09-07 08:15:00', 'groceries', 650.00, 'Fresh Vegetables', 'generic', 'DEMO-007'),
        ('2025-09-08 13:40:00', 'entertainment', 500.00, 'Movie Tickets', 'paytm', 'DEMO-008'),
        ('2025-09-09 10:10:00', 'shopping', 2500.00, 'Clothing Purchase', 'amazon', 'DEMO-009'),
        ('2025-09-10 17:30:00', 'transport', 250.00, 'Taxi Ride', 'gpay', 'DEMO-010'),
    ]
    
    # Insert demo data
    for expense in demo_expenses:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO expenses 
                (tx_datetime, exp_type, total_amount, note, source, txn_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', expense)
        except sqlite3.IntegrityError:
            pass  # Skip if already exists
    
    conn.commit()
    conn.close()
    
    print("✅ Demo data setup complete!")
    print(f"📊 Database ready at: {db_path}")
    print("🚀 You can now start the backend and frontend servers")

if __name__ == "__main__":
    setup_demo_data()