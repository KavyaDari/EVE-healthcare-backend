from django.db import models
from django.conf import settings
from apps.diagnostics.models import DiagnosticCentre, DiagnosticTest

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bookings')
    diagnostic_centre = models.ForeignKey(DiagnosticCentre, on_delete=models.PROTECT, related_name='bookings')
    diagnostic_test = models.ForeignKey(DiagnosticTest, on_delete=models.PROTECT, related_name='bookings')
    appointment_datetime = models.DateTimeField()
    
    # Financial snapshot
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['appointment_datetime']),
        ]

    def __str__(self):
        return f"Booking {self.id} - {self.user.email} - {self.status}"
