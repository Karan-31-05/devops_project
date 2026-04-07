"""
Custom Email Backend for authentication
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from main_app.models import Faculty_Profile


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        login_id = (username or '').strip()
        if not login_id:
            return None

        try:
            user = UserModel.objects.get(email=login_id)
        except UserModel.DoesNotExist:
            user = None

        # Fallback to faculty staff ID login.
        if user is None:
            faculty = Faculty_Profile.objects.select_related('user').filter(
                staff_id__iexact=login_id
            ).first()
            if faculty:
                user = faculty.user

        if user and user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
