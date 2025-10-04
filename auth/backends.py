from core.models import User
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None

        # Use filter to handle multiple users with same email, get first active user
        users = User.objects.filter(Q(email__iexact=email)).filter(is_active=True)
        for user in users:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
