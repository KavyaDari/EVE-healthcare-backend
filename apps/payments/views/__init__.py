from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from ..selectors import get_user_payment
from ..services import initialize_payment, simulate_payment, process_webhook
from ..serializers import (
    PaymentInitSerializer, PaymentReadSerializer, 
    PaymentSimulateSerializer, WebhookPayloadSerializer
)
from drf_spectacular.utils import extend_schema


class PaymentInitializeView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        request=PaymentInitSerializer,
        responses={201: PaymentReadSerializer}
    )
    def post(self, request):
        serializer = PaymentInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment = initialize_payment(
            user=request.user, 
            booking_id=serializer.validated_data['booking_id']
        )
        
        return Response(PaymentReadSerializer(payment).data, status=status.HTTP_201_CREATED)

class PaymentSimulateView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        request=PaymentSimulateSerializer,
        responses={200: PaymentReadSerializer}
    )
    def post(self, request, pk):
        serializer = PaymentSimulateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment = get_user_payment(request.user, pk)
        payment = simulate_payment(payment, serializer.validated_data['result'])
        
        return Response(PaymentReadSerializer(payment).data)

class WebhookView(APIView):
    permission_classes = [AllowAny]  # Provider callback
    @extend_schema(
        request=WebhookPayloadSerializer,
        responses={200: dict}
    )
    def post(self, request):
        serializer = WebhookPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        process_webhook(serializer.validated_data)
        
        # Always return 200 OK so provider stops retrying successfully processed or rejected payloads
        return Response({"received": True}, status=status.HTTP_200_OK)
