from django.shortcuts import get_object_or_404
from ..models import Payment

def get_user_payment(user, payment_id):
    return get_object_or_404(Payment, id=payment_id, booking__user=user)
