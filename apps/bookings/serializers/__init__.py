from rest_framework import serializers
from ..models import Booking

class BookingReadSerializer(serializers.ModelSerializer):
    diagnostic_centre_name = serializers.CharField(source='diagnostic_centre.name', read_only=True)
    diagnostic_test_name = serializers.CharField(source='diagnostic_test.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = (
            'id', 'diagnostic_centre', 'diagnostic_centre_name',
            'diagnostic_test', 'diagnostic_test_name',
            'appointment_datetime', 'amount', 'status',
            'created_at', 'updated_at'
        )

class BookingCreateSerializer(serializers.Serializer):
    diagnostic_centre = serializers.IntegerField()
    diagnostic_test = serializers.IntegerField()
    appointment_datetime = serializers.DateTimeField()
