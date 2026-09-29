import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.diagnostics.models import DiagnosticCentre, DiagnosticTest, CentreTest
from apps.bookings.models import Booking

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def auth_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = User.objects.create_user(email="patient@example.com", password="Password123!")
    client.force_authenticate(user=user)
    client.user = user
    return client

@pytest.fixture
def other_auth_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = User.objects.create_user(email="other@example.com", password="Password123!")
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def test_data():
    centre = DiagnosticCentre.objects.create(name="Apollo", location="Noida")
    test_item = DiagnosticTest.objects.create(name="CBC")
    ct = CentreTest.objects.create(centre=centre, test=test_item, price="500.00")
    
    centre2 = DiagnosticCentre.objects.create(name="Max", location="Delhi")
    
    return {
        "centre": centre,
        "test": test_item,
        "ct": ct,
        "unlinked_centre": centre2
    }

def test_booking_creation_success(auth_client, test_data):
    url = reverse('booking_list_create')
    future_date = timezone.now() + timedelta(days=1)
    
    data = {
        "diagnostic_centre": test_data['centre'].id,
        "diagnostic_test": test_data['test'].id,
        "appointment_datetime": future_date.isoformat()
    }
    
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['amount'] == "500.00"
    assert response.data['status'] == Booking.Status.PENDING

def test_booking_historical_price_snapshot(auth_client, test_data):
    # 1. Price is 500
    future_date = timezone.now() + timedelta(days=1)
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=test_data['centre'],
        diagnostic_test=test_data['test'],
        appointment_datetime=future_date,
        amount=test_data['ct'].price
    )
    
    assert float(booking.amount) == 500.0
    
    # 2. Change CT price to 700
    test_data['ct'].price = 700
    test_data['ct'].save()
    
    # 3. Retrieve booking
    url = reverse('booking_detail', args=[booking.id])
    response = auth_client.get(url)
    
    # Existing booking MUST still be 500.00
    assert response.data['amount'] == "500.00"

def test_booking_unlinked_centre_test_rejected(auth_client, test_data):
    url = reverse('booking_list_create')
    future_date = timezone.now() + timedelta(days=1)
    
    data = {
        "diagnostic_centre": test_data['unlinked_centre'].id,
        "diagnostic_test": test_data['test'].id,
        "appointment_datetime": future_date.isoformat()
    }
    
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not available at the selected centre" in response.data['detail']

def test_booking_past_datetime_rejected(auth_client, test_data):
    url = reverse('booking_list_create')
    past_date = timezone.now() - timedelta(days=1)
    
    data = {
        "diagnostic_centre": test_data['centre'].id,
        "diagnostic_test": test_data['test'].id,
        "appointment_datetime": past_date.isoformat()
    }
    
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "past" in response.data['appointment_datetime']

def test_client_cannot_inject_amount(auth_client, test_data):
    url = reverse('booking_list_create')
    future_date = timezone.now() + timedelta(days=1)
    
    data = {
        "diagnostic_centre": test_data['centre'].id,
        "diagnostic_test": test_data['test'].id,
        "appointment_datetime": future_date.isoformat(),
        "amount": "1.00",
        "status": "CONFIRMED"
    }
    
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    # Amount and status MUST be controlled by server
    assert response.data['amount'] == "500.00"
    assert response.data['status'] == Booking.Status.PENDING

def test_booking_ownership_anti_enumeration(auth_client, other_auth_client, test_data):
    # User A creates booking
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=test_data['centre'],
        diagnostic_test=test_data['test'],
        appointment_datetime=timezone.now() + timedelta(days=1),
        amount=500
    )
    
    # User B tries to get User A's booking
    url = reverse('booking_detail', args=[booking.id])
    response = other_auth_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # User B tries to cancel User A's booking
    url_cancel = reverse('booking_cancel', args=[booking.id])
    response = other_auth_client.post(url_cancel)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_booking_cancel_pending_succeeds(auth_client, test_data):
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=test_data['centre'],
        diagnostic_test=test_data['test'],
        appointment_datetime=timezone.now() + timedelta(days=1),
        amount=500,
        status=Booking.Status.PENDING
    )
    
    url = reverse('booking_cancel', args=[booking.id])
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == Booking.Status.CANCELLED

def test_booking_cancel_confirmed_succeeds(auth_client, test_data):
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=test_data['centre'],
        diagnostic_test=test_data['test'],
        appointment_datetime=timezone.now() + timedelta(days=1),
        amount=500,
        status=Booking.Status.CONFIRMED
    )
    
    url = reverse('booking_cancel', args=[booking.id])
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == Booking.Status.CANCELLED

def test_booking_cancel_failed_fails(auth_client, test_data):
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=test_data['centre'],
        diagnostic_test=test_data['test'],
        appointment_datetime=timezone.now() + timedelta(days=1),
        amount=500,
        status=Booking.Status.FAILED
    )
    
    url = reverse('booking_cancel', args=[booking.id])
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot cancel" in response.data['detail']
