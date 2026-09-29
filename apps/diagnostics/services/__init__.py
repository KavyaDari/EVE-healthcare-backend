from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from ..models import DiagnosticCentre, DiagnosticTest, CentreTest

def create_centre(name, location) -> DiagnosticCentre:
    return DiagnosticCentre.objects.create(name=name, location=location)

def update_centre(centre, **data) -> DiagnosticCentre:
    for field, value in data.items():
        setattr(centre, field, value)
    centre.save()
    return centre

def delete_centre(centre):
    centre.delete()

def create_test(name, description) -> DiagnosticTest:
    try:
        with transaction.atomic():
            return DiagnosticTest.objects.create(name=name, description=description)
    except IntegrityError:
        raise ValidationError({"name": "A test with this name already exists."})

def update_test(test, **data) -> DiagnosticTest:
    for field, value in data.items():
        setattr(test, field, value)
    try:
        with transaction.atomic():
            test.save()
    except IntegrityError:
        raise ValidationError({"name": "A test with this name already exists."})
    return test

def delete_test(test):
    test.delete()

def add_test_to_centre(centre, test, price) -> CentreTest:
    try:
        with transaction.atomic():
            return CentreTest.objects.create(centre=centre, test=test, price=price)
    except IntegrityError:
        raise ValidationError({"detail": "This test is already associated with this centre."})

def update_centre_test_price(centre_test, price) -> CentreTest:
    centre_test.price = price
    centre_test.save()
    return centre_test

def remove_test_from_centre(centre_test):
    centre_test.delete()
