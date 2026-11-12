import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def isolated_activities():
    original_activities = copy.deepcopy(activities)
    activities.clear()
    activities.update(
        {
            "Test Club": {
                "description": "A test activity",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 2,
                "participants": ["existing@example.com"],
            }
        }
    )
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "Test Club": {
            "description": "A test activity",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": ["existing@example.com"],
        }
    }


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Test Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Test Club"}
    assert "new@example.com" in activities["Test Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_for_existing_participant(client):
    response = client.post(
        "/activities/Test Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Test Club/participants",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Test Club"
    }
    assert "existing@example.com" not in activities["Test Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Test Club/participants",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
