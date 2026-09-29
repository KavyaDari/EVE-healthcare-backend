from decimal import Decimal
from rest_framework import serializers
from ..models import DiagnosticCentre, DiagnosticTest, CentreTest

class DiagnosticCentreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticCentre
        fields = ('id', 'name', 'location', 'created_at', 'updated_at')

class DiagnosticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = ('id', 'name', 'description', 'created_at', 'updated_at')

class CentreTestReadSerializer(serializers.ModelSerializer):
    test = DiagnosticTestSerializer(read_only=True)
    
    class Meta:
        model = CentreTest
        fields = ('id', 'test', 'price', 'created_at', 'updated_at')

class CentreTestWriteSerializer(serializers.Serializer):
    test_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
    
class CentreTestUpdateSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
