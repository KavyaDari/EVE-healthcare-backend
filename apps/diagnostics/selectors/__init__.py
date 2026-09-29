from django.shortcuts import get_object_or_404
from ..models import DiagnosticCentre, DiagnosticTest, CentreTest

def list_centres():
    return DiagnosticCentre.objects.all().order_by('-id')

def get_centre(centre_id):
    return get_object_or_404(DiagnosticCentre, id=centre_id)

def list_tests():
    return DiagnosticTest.objects.all().order_by('-id')

def get_test(test_id):
    return get_object_or_404(DiagnosticTest, id=test_id)

def list_centre_tests(centre_id):
    # select_related avoids N+1 when accessing the test's name/description
    return CentreTest.objects.filter(centre_id=centre_id).select_related('test').order_by('test__name')

def get_centre_test(centre_id, test_id):
    return get_object_or_404(CentreTest, centre_id=centre_id, test_id=test_id)
