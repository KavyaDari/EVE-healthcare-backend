import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.diagnostics.models import DiagnosticCentre, DiagnosticTest, CentreTest
from apps.bookings.models import Booking
from apps.payments.models import Payment, PaymentWebhookEvent

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
def test_booking(auth_client):
    centre = DiagnosticCentre.objects.create(name="Apollo", location="Noida")
    test_item = DiagnosticTest.objects.create(name="CBC")
    CentreTest.objects.create(centre=centre, test=test_item, price="500.00")
    
    booking = Booking.objects.create(
        user=auth_client.user,
        diagnostic_centre=centre,
        diagnostic_test=test_item,
        appointment_datetime=timezone.now() + timedelta(days=1),
        amount="500.00",
        status=Booking.Status.PENDING
    )
    return booking

def test_payment_initialization(auth_client, test_booking):
    url = reverse('payment_init')
    response = auth_client.post(url, {"booking_id": test_booking.id})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['amount'] == "500.00"
    assert response.data['status'] == "PENDING"
    assert response.data['provider_payment_id'].startswith("pay_")

def test_payment_initialization_not_pending(auth_client, test_booking):
    test_booking.status = Booking.Status.CANCELLED
    test_booking.save()
    
    url = reverse('payment_init')
    response = auth_client.post(url, {"booking_id": test_booking.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_payment_duplicate_initialization(auth_client, test_booking):
    url = reverse('payment_init')
    auth_client.post(url, {"booking_id": test_booking.id})
    # second time
    response = auth_client.post(url, {"booking_id": test_booking.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.data['detail']

def test_payment_ownership(other_auth_client, test_booking):
    url = reverse('payment_init')
    response = other_auth_client.post(url, {"booking_id": test_booking.id})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_simulation_success(auth_client, test_booking):
    url_init = reverse('payment_init')
    init_res = auth_client.post(url_init, {"booking_id": test_booking.id})
    payment_id = init_res.data['id']
    
    url_sim = reverse('payment_simulate', args=[payment_id])
    res_sim = auth_client.post(url_sim, {"result": "SUCCESS"})
    assert res_sim.status_code == status.HTTP_200_OK
    assert res_sim.data['status'] == "SUCCESS"
    
    test_booking.refresh_from_db()
    assert test_booking.status == Booking.Status.CONFIRMED

def test_webhook_idempotency(auth_client, test_booking):
    init_res = auth_client.post(reverse('payment_init'), {"booking_id": test_booking.id})
    provider_id = init_res.data['provider_payment_id']
    
    url_webhook = reverse('payment_webhook')
    payload = {
        "event_id": "evt_duplicate_123",
        "provider_payment_id": provider_id,
        "status": "SUCCESS"
    }
    
    # Fire first webhook
    res1 = auth_client.post(url_webhook, payload)
    assert res1.status_code == status.HTTP_200_OK
    assert PaymentWebhookEvent.objects.count() == 1
    
    test_booking.refresh_from_db()
    assert test_booking.status == Booking.Status.CONFIRMED
    
    # Fire second webhook with IDENTICAL event_id
    res2 = auth_client.post(url_webhook, payload)
    assert res2.status_code == status.HTTP_200_OK
    
    # Should STILL be 1 event record because of IntegrityError catching (idempotent no-op)
    assert PaymentWebhookEvent.objects.count() == 1

def test_webhook_contradictory_late_event(auth_client, test_booking):
    init_res = auth_client.post(reverse('payment_init'), {"booking_id": test_booking.id})
    provider_id = init_res.data['provider_payment_id']
    url_webhook = reverse('payment_webhook')
    
    # Event 1: SUCCESS
    auth_client.post(url_webhook, {
        "event_id": "evt_1",
        "provider_payment_id": provider_id,
        "status": "SUCCESS"
    })
    
    # Event 2: FAILED (late, contradictory)
    auth_client.post(url_webhook, {
        "event_id": "evt_2",
        "provider_payment_id": provider_id,
        "status": "FAILED"
    })
    
    # State MUST remain SUCCESS/CONFIRMED (terminal state protection)
    test_booking.refresh_from_db()
    assert test_booking.status == Booking.Status.CONFIRMED
    assert test_booking.payment.status == Payment.Status.SUCCESS
    
    # But both events should be logged
    assert PaymentWebhookEvent.objects.count() == 2

def test_critical_inconsistency_prevention(auth_client, test_booking):
    # Tests that the payment/booking are synced atomically
    init_res = auth_client.post(reverse('payment_init'), {"booking_id": test_booking.id})
    provider_id = init_res.data['provider_payment_id']
    
    # Valid transition
    auth_client.post(reverse('payment_webhook'), {
        "event_id": "evt_sync_check",
        "provider_payment_id": provider_id,
        "status": "FAILED"
    })
    
    test_booking.refresh_from_db()
    
    # They MUST match
    assert test_booking.status == Booking.Status.FAILED
    assert test_booking.payment.status == Payment.Status.FAILED
    # It is impossible for one to be FAILED and another to be SUCCESS/CONFIRMED 
    # due to the atomic block in the service updating them simultaneously.

from unittest.mock import patch

def test_webhook_failed_to_success_ignored(auth_client, test_booking):
    init_res = auth_client.post(reverse('payment_init'), {"booking_id": test_booking.id})
    provider_id = init_res.data['provider_payment_id']
    
    # Event 1: FAILED
    auth_client.post(reverse('payment_webhook'), {
        "event_id": "evt_f1", "provider_payment_id": provider_id, "status": "FAILED"
    })
    
    # Event 2: SUCCESS
    auth_client.post(reverse('payment_webhook'), {
        "event_id": "evt_s2", "provider_payment_id": provider_id, "status": "SUCCESS"
    })
    
    test_booking.refresh_from_db()
    assert test_booking.status == Booking.Status.FAILED
    assert test_booking.payment.status == Payment.Status.FAILED

def test_webhook_atomicity_rollback(auth_client, test_booking):
    init_res = auth_client.post(reverse('payment_init'), {"booking_id": test_booking.id})
    provider_id = init_res.data['provider_payment_id']
    
    with patch('apps.payments.models.Payment.save', side_effect=Exception("DB Error")):
        try:
            auth_client.post(reverse('payment_webhook'), {
                "event_id": "evt_atomicity",
                "provider_payment_id": provider_id,
                "status": "SUCCESS"
            })
        except Exception:
            pass
            
    test_booking.refresh_from_db()
    assert test_booking.status == Booking.Status.PENDING
    assert test_booking.payment.status == Payment.Status.PENDING
    assert PaymentWebhookEvent.objects.filter(event_id="evt_atomicity").count() == 0

def test_payment_amount_derived_from_booking(auth_client, test_booking):
    url = reverse('payment_init')
    response = auth_client.post(url, {"booking_id": test_booking.id, "amount": "999.00"})
    
    assert response.status_code == status.HTTP_201_CREATED
    assert float(response.data['amount']) == 500.0

def test_webhook_malformed_payload(auth_client, test_booking):
    response = auth_client.post(reverse('payment_webhook'), {"event_id": "test"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_webhook_unknown_provider_id_handled(auth_client):
    response = auth_client.post(reverse('payment_webhook'), {
        "event_id": "evt_unknown",
        "provider_payment_id": "pay_unknown123",
        "status": "SUCCESS"
    })
    assert response.status_code == status.HTTP_200_OK
    assert PaymentWebhookEvent.objects.count() == 0
