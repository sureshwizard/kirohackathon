from fastapi.testclient import TestClient
from backend_ingest.app import app

client = TestClient(app)

def test_preview_generic():
    csv_content = "Date,Type,Amount,Note,ID\n2025-09-01,misc,123.45,TestNote,TXN1\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    r = client.post("/preview_csv", data={"source": "generic"}, files=files)
    assert r.status_code == 200
    data = r.json()
    assert "parsed" in data
    assert data["parsed"][0]["total_amount"] == 123.45
