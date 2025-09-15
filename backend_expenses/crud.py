from sqlalchemy.orm import Session
from . import models

def create_expense(db: Session, exp: models.ExpenseCreate):
    db_exp = models.Expense(
        tx_datetime=exp.tx_datetime,
        exp_type=exp.exp_type,
        total_amount=exp.total_amount,
        note=exp.note
    )
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)

    # add items
    for it in exp.items:
        db_item = models.ExpenseItem(
            expense_id=db_exp.id,
            quantity=it.quantity,
            amount=it.amount
        )
        db.add(db_item)
    db.commit()
    return db_exp

def get_expenses(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Expense).offset(skip).limit(limit).all()
