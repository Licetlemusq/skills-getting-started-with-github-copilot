"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Save original state
    original_activities = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    
    yield
    
    # Restore original state
    for activity_name, activity_data in activities.items():
        activity_data["participants"] = original_activities[activity_name]["participants"]


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have activities
        assert len(data) > 0
        
        # Check structure of an activity
        assert "Basketball" in data
        activity = data["Basketball"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_has_participants(self, client):
        """Test that activities have participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Check Basketball has at least one participant
        assert len(data["Basketball"]["participants"]) > 0


class TestSignup:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant"""
        activity_name = "Basketball"
        email = "newstudent@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        
        # Verify participant was added
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test that a participant cannot sign up twice"""
        activity_name = "Basketball"
        email = "alex@mergington.edu"  # Already signed up
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRemoveParticipant:
    """Test DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test removing a participant from an activity"""
        activity_name = "Basketball"
        email = "alex@mergington.edu"  # Already signed up
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        
        # Verify participant was removed
        response = client.get("/activities")
        activities_data = response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_remove_nonexistent_participant(self, client, reset_activities):
        """Test removing a participant that doesn't exist"""
        activity_name = "Basketball"
        email = "notstudent@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_remove_participant_from_nonexistent_activity(self, client, reset_activities):
        """Test removing a participant from a non-existent activity"""
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestIntegration:
    """Integration tests for full workflows"""
    
    def test_signup_and_remove_workflow(self, client, reset_activities):
        """Test complete workflow: signup, check, and remove"""
        activity_name = "Tennis Club"
        email = "tennisplayer@mergington.edu"
        
        # Sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Remove
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
    
    def test_multiple_participants_workflow(self, client, reset_activities):
        """Test adding multiple participants to an activity"""
        activity_name = "Art Class"
        participants = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up multiple participants
        for email in participants:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are signed up
        response = client.get("/activities")
        activity_participants = response.json()[activity_name]["participants"]
        for email in participants:
            assert email in activity_participants
        
        # Remove one participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{participants[0]}"
        )
        assert response.status_code == 200
        
        # Verify one was removed and others remain
        response = client.get("/activities")
        activity_participants = response.json()[activity_name]["participants"]
        assert participants[0] not in activity_participants
        assert participants[1] in activity_participants
        assert participants[2] in activity_participants
