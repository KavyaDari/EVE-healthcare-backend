from django.db import transaction, IntegrityError
from django.utils import timezone
import uuid
from rest_framework.exceptions import ValidationError
from ..models import Payment, PaymentWebhookEvent
from apps.bookings.models import Booking
from apps.bookings.selectors import get_user_booking_for_update

def initialize_payment(user, booking_id) -> Payment:
    with transaction.atomic():
        # Lock booking first
        booking = get_user_booking_for_update(user, booking_id)
        
        if booking.status != Booking.Status.PENDING:
            raise ValidationError({"detail": f"Cannot initialize payment for a {booking.status} booking."})
            
        if hasattr(booking, 'payment'):
            raise ValidationError({"detail": "A payment already exists for this booking."})
            
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.amount,
            status=Payment.Status.PENDING
        )
        return payment

def process_webhook(payload: dict):
    event_id = payload.get('event_id')
    provider_payment_id = payload.get('provider_payment_id')
    event_status = payload.get('status')
    
    if not event_id or not provider_payment_id or not event_status:
        raise ValidationError("Missing required webhook fields.")

    with transaction.atomic():
        # 1. Resolve Provider Payment and Lock Booking -> Payment
        try:
            booking = Booking.objects.select_for_update().get(payment__provider_payment_id=provider_payment_id)
            payment = Payment.objects.select_for_update().get(provider_payment_id=provider_payment_id)
        except (Booking.DoesNotExist, Payment.DoesNotExist):
            # Unknown provider ID. Safe no-op.
            return
            
        # 2. Attempt Unique Event Insertion (Idempotency)
        try:
            with transaction.atomic():
                event = PaymentWebhookEvent.objects.create(
                    event_id=event_id,
                    provider_payment_id=provider_payment_id,
                    status=event_status,
                    payload=payload,
                    payment=payment
                )
        except IntegrityError:
            # Duplicate event ID, safe idempotent no-op
            return

        # 3. Terminal State Protection
        if payment.status in [Payment.Status.SUCCESS, Payment.Status.FAILED]:
            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])
            return
            
        # 4. Apply State Transition
        if event_status == 'SUCCESS':
            payment.status = Payment.Status.SUCCESS
            booking.status = Booking.Status.CONFIRMED
        elif event_status == 'FAILED':
            payment.status = Payment.Status.FAILED
            booking.status = Booking.Status.FAILED
        else:
            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])
            return
            
        # 5. Save and commit
        payment.save(update_fields=['status', 'updated_at'])
        booking.save(update_fields=['status', 'updated_at'])
        
        event.processed_at = timezone.now()
        event.save(update_fields=['processed_at'])

def simulate_payment(payment, result) -> Payment:
    # Build webhook-like payload to exercise identical logic
    payload = {
        "event_id": f"evt_sim_{uuid.uuid4().hex}",
        "provider_payment_id": payment.provider_payment_id,
        "status": result
    }
    process_webhook(payload)
    payment.refresh_from_db()
    return payment
