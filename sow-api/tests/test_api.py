"""Unit tests for the sow-api package."""
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user
from app.models import WaffleReview
import pytest

def get_mock_user():
    return {"preferred_username": "test_user"}

client = TestClient(app)
app.dependency_overrides[get_current_user] = get_mock_user



def test_create_review():
    response = client.post(
        "/api/waffle/reviews",
        json=WaffleReview(
            restaurant="John Doe",
            review="Delicious!",
    ).model_dump(),
        headers={
            "Authorization": "Bearer test_token"
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Review submitted successfully!",
        "user": "test_user"
    }


def test_get_userinfo():
    response = client.get(
        "/userinfo",
        headers={
            "Authorization": "Bearer test_token"
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "preferred_username": "test_user"
    }