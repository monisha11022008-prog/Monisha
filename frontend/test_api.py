from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "LegalEase AI"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_generate_demo_document():
    response = client.post(
        "/generate",
        json={
            "document_type": "NDA",
            "parties": (
                "Alice (Disclosing Party), "
                "Beta Ltd (Receiving Party)"
            ),
            "terms": (
                "Confidentiality applies; "
                "Return confidential information "
                "on request"
            ),
            "effective_date": "2026-09-29",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "document" in data
    assert len(data["document"]) > 50


def test_generate_rejects_missing_field():
    response = client.post(
        "/generate",
        json={
            "document_type": "NDA",
            "parties": "Alice and Beta Ltd",
            "terms": "Confidentiality applies",
        },
    )

    assert response.status_code == 422