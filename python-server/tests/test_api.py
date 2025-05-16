import sys
from fastapi.testclient import TestClient
import pytest

# Add parent directory to path to allow imports from app
sys.path.insert(0, "../")

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint(client):
    response = client.post(
        "/api/chat/message",
        json={"message": "Test message", "conversation_id": None}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "conversation_id" in response.json()


def test_jira_issues_endpoint(client):
    response = client.get("/api/jira/issues")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert "key" in response.json()[0]
