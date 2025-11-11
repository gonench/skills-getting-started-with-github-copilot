"""Tests for the Mergington High School Activities API"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Soccer Team" in activities
        
    def test_activity_structure(self):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            
    def test_activities_have_initial_participants(self):
        """Test that activities have some initial participants"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert len(activity_data["participants"]) > 0


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]
        
    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "newtestuser@mergington.edu"
        
        # Get initial participants
        response = client.get("/activities")
        initial_participants = response.json()["Math Club"]["participants"].copy()
        
        # Sign up
        signup_response = client.post(
            f"/activities/Math Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        new_participants = response.json()["Math Club"]["participants"]
        assert email in new_participants
        assert len(new_participants) == len(initial_participants) + 1
        
    def test_signup_duplicate_email_fails(self):
        """Test that signing up with an already registered email fails"""
        email = "duplicate@mergington.edu"
        
        # Sign up once
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        # Try to sign up again (should fail because already in an activity)
        response2 = client.post(
            f"/activities/Drama Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unreg_test@mergington.edu"
        
        # First sign up
        signup_response = client.post(
            f"/activities/Swimming Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.post(
            f"/activities/Swimming Club/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        result = unregister_response.json()
        assert "message" in result
        assert email in result["message"]
        
    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal_test@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Art Club/signup?email={email}")
        
        # Verify participant is there
        response = client.get("/activities")
        assert email in response.json()["Art Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Art Club/unregister?email={email}")
        
        # Verify participant is gone
        response = client.get("/activities")
        assert email not in response.json()["Art Club"]["participants"]
        
    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    def test_unregister_nonexistent_participant_fails(self):
        """Test that unregistering a non-existent participant fails"""
        response = client.post(
            "/activities/Chess Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
