from fastapi.testclient import TestClient
from backend_expenses.app import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Welcome" in r.json()["message"]

def test_add_expense():
    payload = {
        "tx_datetime": "2025-09-01T10:00:00",
        "exp_type": "groceries",
        "total_amount": 120.5,
        "note": "test expense",
        "items": [
            {"quantity": 2, "amount": 60.25}
        ]
    }
    r = client.post("/expenses/", json=payload)
    assert r.status_code == 200
    assert r.json()["exp_type"] == "groceries"
