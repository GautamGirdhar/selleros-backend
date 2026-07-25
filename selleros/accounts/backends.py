from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend:

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("email") or "").strip()

        if not identifier:
            return None

        try:
            user = User.objects.get(
                Q(email__iexact=identifier) | Q(phone_number=identifier)
            )

        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):

        try:
            return User.objects.get(pk=user_id)

        except User.DoesNotExist:
            return None


# Kept as an alias while older running processes/configuration still reference it.
EmailBackend = EmailOrPhoneBackend
