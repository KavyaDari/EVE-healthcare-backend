from django.urls import path
from .views import TestListCreateView, TestDetailView

urlpatterns = [
    path('', TestListCreateView.as_view(), name='test_list_create'),
    path('<int:pk>/', TestDetailView.as_view(), name='test_detail'),
]
