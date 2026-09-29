from django.db import models
import uuid

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        
    booking = models.OneToOneField('bookings.Booking', on_delete=models.PROTECT, related_name='payment')
    provider_payment_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.provider_payment_id:
            # Generate a unique simulated provider ID
            self.provider_payment_id = f"pay_{uuid.uuid4().hex}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking_id} - {self.status}"

class PaymentWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    provider_payment_id = models.CharField(max_length=255)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
