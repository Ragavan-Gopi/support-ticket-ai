import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_health():
    response = client.get("/health/")
    assert response.status_code == 200

def test_query_status():
    response = client.get("/query/status")
    assert response.status_code == 200
    data = response.json()
    assert "ticket_count" in data

def test_anomalies_status():
    response = client.get("/anomalies/status")
    assert response.status_code == 200

def test_anomalies_summary():
    response = client.get("/anomalies/summary")
    assert response.status_code == 200

def test_anomalies_analytics():
    response = client.get("/anomalies/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data.get("total_tickets") == 500

def test_query_retrieve_validation_error():
    response = client.post("/query/retrieve", json={"query": "", "top_k": 2})
    # Fastapi validation is usually 422, but we also have a manual check that returns 400
    assert response.status_code in (400, 422)

def test_query_index_validation_error():
    # Provide invalid limit to trigger validation error without hitting Ollama
    response = client.post("/query/index", json={"limit": 0})
    assert response.status_code == 422

def test_query_ask_hybrid_total_tickets():
    response = client.post("/query/ask", json={"question": "How many total tickets are there?", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["answer_type"] == "analytics"
    assert "500" in data["answer"]
    assert "SQLite analytics" in data["sources"]

def test_query_ask_hybrid_unsupported_rating():
    response = client.post("/query/ask", json={"question": "Which agent has the lowest average customer rating?", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["answer_type"] == "analytics"
    # Even though we might compute it, ensure it responds cleanly and offline
    assert "customer rating" in data["answer"].lower()

def test_query_ask_validation_error():
    response = client.post("/query/ask", json={"question": "", "top_k": 2})
    assert response.status_code in (400, 422)
