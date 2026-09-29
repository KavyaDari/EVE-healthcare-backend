import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

def test_environment_loads():
    assert True

def test_custom_user_model():
    User = get_user_model()
    assert User.__name__ == 'User'
    assert User.objects.count() == 0
