from django.shortcuts import get_object_or_404
from ..models import Booking

def list_user_bookings(user):
    return Booking.objects.filter(user=user).select_related(
        'diagnostic_centre', 'diagnostic_test'
    ).order_by('-created_at')

def get_user_booking(user, booking_id):
    return get_object_or_404(
        Booking.objects.select_related('diagnostic_centre', 'diagnostic_test'),
        id=booking_id,
        user=user
    )

def get_user_booking_for_update(user, booking_id):
    return get_object_or_404(
        Booking.objects.select_for_update(),
        id=booking_id,
        user=user
    )
