import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.diagnostics.models import DiagnosticCentre, DiagnosticTest, CentreTest

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def auth_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = User.objects.create_user(email="patient@example.com", password="Password123!")
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def staff_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = User.objects.create_superuser(email="admin@example.com", password="Password123!")
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def centre():
    return DiagnosticCentre.objects.create(name="Apollo", location="Noida")

@pytest.fixture
def test_item():
    return DiagnosticTest.objects.create(name="CBC")

def test_auth_client_can_list_centres(auth_client, centre):
    url = reverse('centre_list_create')
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

def test_auth_client_cannot_create_centre(auth_client):
    url = reverse('centre_list_create')
    response = auth_client.post(url, {"name": "Max", "location": "Delhi"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_staff_client_can_create_centre(staff_client):
    url = reverse('centre_list_create')
    response = staff_client.post(url, {"name": "Max", "location": "Delhi"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == "Max"

def test_staff_client_can_update_centre(staff_client, centre):
    url = reverse('centre_detail', args=[centre.id])
    response = staff_client.patch(url, {"location": "Gurgaon"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data['location'] == "Gurgaon"

def test_staff_client_can_associate_test_to_centre(staff_client, centre, test_item):
    url = reverse('centre_test_list_create', args=[centre.id])
    response = staff_client.post(url, {"test_id": test_item.id, "price": "500.00"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['price'] == "500.00"

def test_duplicate_centre_test_rejected(staff_client, centre, test_item):
    CentreTest.objects.create(centre=centre, test=test_item, price=500.00)
    url = reverse('centre_test_list_create', args=[centre.id])
    response = staff_client.post(url, {"test_id": test_item.id, "price": "600.00"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_negative_price_rejected(staff_client, centre, test_item):
    url = reverse('centre_test_list_create', args=[centre.id])
    response = staff_client.post(url, {"test_id": test_item.id, "price": "-500.00"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_auth_client_can_list_centre_tests(auth_client, centre, test_item):
    CentreTest.objects.create(centre=centre, test=test_item, price=500.00)
    url = reverse('centre_test_list_create', args=[centre.id])
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['test']['name'] == "CBC"
    assert response.data[0]['price'] == "500.00"

def test_staff_can_update_price(staff_client, centre, test_item):
    ct = CentreTest.objects.create(centre=centre, test=test_item, price=500.00)
    url = reverse('centre_test_detail', args=[centre.id, test_item.id])
    response = staff_client.patch(url, {"price": "600.00"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data['price'] == "600.00"

def test_staff_can_delete_centre_test(staff_client, centre, test_item):
    ct = CentreTest.objects.create(centre=centre, test=test_item, price=500.00)
    url = reverse('centre_test_detail', args=[centre.id, test_item.id])
    response = staff_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not CentreTest.objects.filter(id=ct.id).exists()
