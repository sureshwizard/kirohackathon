from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel
from datetime import datetime

Base = declarative_base()

# ---------- SQLAlchemy models ----------
class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    tx_datetime = Column(DateTime, default=datetime.utcnow)
    exp_type = Column(String, index=True)   # groceries, wifi, etc.
    total_amount = Column(Float)
    note = Column(String, nullable=True)
# inside Expense class in backend_expenses/models.py
    source = Column(String, nullable=True, index=True)
    txn_id = Column(String, nullable=True, index=True)

    items = relationship("ExpenseItem", back_populates="expense")

class ExpenseItem(Base):
    __tablename__ = "expense_items"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    quantity = Column(Float)
    amount = Column(Float)

    expense = relationship("Expense", back_populates="items")

# ---------- Pydantic schemas ----------
class ExpenseItemCreate(BaseModel):
    quantity: float
    amount: float

class ExpenseCreate(BaseModel):
    tx_datetime: datetime
    exp_type: str
    total_amount: float
    note: str | None = None
    items: list[ExpenseItemCreate] = []

class ExpenseRead(BaseModel):
    id: int
    tx_datetime: datetime
    exp_type: str
    total_amount: float
    note: str | None
    items: list[ExpenseItemCreate] = []

    class Config:
        orm_mode = True
