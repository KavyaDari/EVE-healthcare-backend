from rest_framework import serializers
from ..models import Payment

class PaymentInitSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()

class PaymentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'booking', 'provider_payment_id', 'amount', 'status', 'created_at', 'updated_at')
        read_only_fields = fields

class PaymentSimulateSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=['SUCCESS', 'FAILED'])

class WebhookPayloadSerializer(serializers.Serializer):
    event_id = serializers.CharField()
    provider_payment_id = serializers.CharField()
    status = serializers.CharField()
