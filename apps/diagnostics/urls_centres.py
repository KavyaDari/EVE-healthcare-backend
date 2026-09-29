from django.urls import path
from .views import CentreListCreateView, CentreDetailView, CentreTestListCreateView, CentreTestDetailView

urlpatterns = [
    path('', CentreListCreateView.as_view(), name='centre_list_create'),
    path('<int:pk>/', CentreDetailView.as_view(), name='centre_detail'),
    path('<int:centre_id>/tests/', CentreTestListCreateView.as_view(), name='centre_test_list_create'),
    path('<int:centre_id>/tests/<int:test_id>/', CentreTestDetailView.as_view(), name='centre_test_detail'),
]
