from django.urls import path
from .views import PaymentInitializeView, PaymentSimulateView, WebhookView

urlpatterns = [
    path('', PaymentInitializeView.as_view(), name='payment_init'),
    path('<int:pk>/simulate/', PaymentSimulateView.as_view(), name='payment_simulate'),
    path('webhook/', WebhookView.as_view(), name='payment_webhook'),
]
