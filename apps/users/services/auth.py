from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

def register_user(email: str, password: str) -> User:
    try:
        # Normalize email via the model manager
        email = User.objects.normalize_email(email)
        user = User.objects.create_user(email=email, password=password)
        return user
    except IntegrityError:
        raise ValidationError({"email": "User with this email already exists."})
