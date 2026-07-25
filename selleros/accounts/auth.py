from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

User = get_user_model()


def create_tokens(user):
    """
    Generate Access & Refresh JWT tokens
    """

    refresh = RefreshToken.for_user(user)

    refresh["email"] = user.email
    refresh["phone_number"] = user.phone_number
    refresh["full_name"] = user.full_name
    refresh["provider"] = user.auth_provider

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def refresh_access(refresh_token: str):
    """
    Generate new access token using refresh token
    """

    try:
        refresh = RefreshToken(refresh_token)

        return {
            "access": str(refresh.access_token)
        }

    except TokenError:
        raise InvalidToken("Invalid Refresh Token")


def blacklist_token(refresh_token: str):
    """
    Logout user
    """

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True

    except TokenError:
        return False


def verify_access(access_token: str):
    """
    Verify Access Token
    """

    try:
        access = AccessToken(access_token)

        user_id = access["user_id"]

        return User.objects.get(id=user_id)

    except Exception:
        return None


def get_authenticated_user(auth_header: str):
    """
    Authorization: Bearer <token>
    """

    if not auth_header:
        return None

    token = auth_header.replace("Bearer ", "")

    return verify_access(token)