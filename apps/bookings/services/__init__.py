from django.db import transaction
from django.utils import timezone
from django.http import Http404
from rest_framework.exceptions import ValidationError
from ..models import Booking
from apps.diagnostics.selectors import get_centre_test
from ..selectors import get_user_booking_for_update

def create_booking(user, diagnostic_centre, diagnostic_test, appointment_datetime) -> Booking:
    diagnostic_centre_id = diagnostic_centre
    diagnostic_test_id = diagnostic_test
    if appointment_datetime < timezone.now():
        raise ValidationError({"appointment_datetime": "Appointments cannot be scheduled in the past."})
    
    try:
        centre_test = get_centre_test(diagnostic_centre_id, diagnostic_test_id)
    except Http404:
        raise ValidationError({"detail": "This diagnostic test is not available at the selected centre."})
        
    booking = Booking.objects.create(
        user=user,
        diagnostic_centre_id=diagnostic_centre_id,
        diagnostic_test_id=diagnostic_test_id,
        appointment_datetime=appointment_datetime,
        amount=centre_test.price,
        status=Booking.Status.PENDING
    )
    return booking

def cancel_booking(user, booking_id) -> Booking:
    with transaction.atomic():
        # LOCK -> RECHECK STATE -> TRANSITION
        booking = get_user_booking_for_update(user, booking_id)
        
        if booking.status in [Booking.Status.FAILED, Booking.Status.CANCELLED]:
            raise ValidationError({"detail": f"Cannot cancel a booking in {booking.status} state."})
            
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        return booking
