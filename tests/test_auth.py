import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

def test_successful_signup(api_client):
    url = reverse('signup')
    data = {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['email'] == "newuser@example.com"
    assert "password" not in response.data

def test_duplicate_email_signup(api_client):
    User.objects.create_user(email="test@example.com", password="Password123!")
    url = reverse('signup')
    data = {
        "email": "test@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data

def test_invalid_email(api_client):
    url = reverse('signup')
    data = {
        "email": "not-an-email",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_weak_password(api_client):
    url = reverse('signup')
    data = {
        "email": "test2@example.com",
        "password": "123",
        "password_confirm": "123"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data

def test_password_is_stored_hashed():
    user = User.objects.create_user(email="hash@example.com", password="StrongPassword123!")
    assert user.password != "StrongPassword123!"
    assert user.password.startswith("md5$") or user.check_password("StrongPassword123!")

def test_successful_login(api_client):
    User.objects.create_user(email="login@example.com", password="StrongPassword123!")
    url = reverse('login')
    response = api_client.post(url, {"email": "login@example.com", "password": "StrongPassword123!"})
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

def test_invalid_password(api_client):
    User.objects.create_user(email="login2@example.com", password="StrongPassword123!")
    url = reverse('login')
    response = api_client.post(url, {"email": "login2@example.com", "password": "WrongPassword123!"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "access" not in response.data

def test_invalid_email_combination(api_client):
    url = reverse('login')
    response = api_client.post(url, {"email": "nonexistent@example.com", "password": "StrongPassword123!"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_refresh_token_works(api_client):
    User.objects.create_user(email="refresh@example.com", password="StrongPassword123!")
    login_response = api_client.post(reverse('login'), {"email": "refresh@example.com", "password": "StrongPassword123!"})
    refresh_token = login_response.data["refresh"]
    
    url = reverse('token_refresh')
    response = api_client.post(url, {"refresh": refresh_token})
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data

def test_me_endpoint_works_with_jwt(api_client):
    user = User.objects.create_user(email="me@example.com", password="StrongPassword123!")
    login_response = api_client.post(reverse('login'), {"email": "me@example.com", "password": "StrongPassword123!"})
    access_token = login_response.data["access"]
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    response = api_client.get(reverse('me'))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == "me@example.com"

def test_me_rejects_unauthenticated(api_client):
    response = api_client.get(reverse('me'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
