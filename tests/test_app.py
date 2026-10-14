import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    initial_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", initial_activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_app(client):
    # Arrange
    redirect_url = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == redirect_url


def test_get_activities_returns_seeded_activity_data(client):
    # Arrange
    expected_activity_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Club",
        "Basketball Club",
        "Art Club",
        "Drama Club",
        "Debate Club",
        "Science Club",
    }

    # Act
    response = client.get("/activities")

    # Assert
    activities = response.json()
    assert response.status_code == 200
    assert set(activities) == expected_activity_names
    assert all(
        {"description", "schedule", "max_participants", "participants"}
        <= activity.keys()
        for activity in activities.values()
    )


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in updated_activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_422_when_email_is_missing(client):
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup"
    )

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in updated_activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_succeeds_when_participant_is_absent(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }