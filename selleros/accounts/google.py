import logging

import requests

from django.conf import settings

from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def exchange_code_for_user(code: str) -> dict:
    """
    Exchange Google OAuth authorization code for user information.

    Returns:
        {
            "email": str,
            "name": str,
            "picture": str | None,
            "email_verified": bool,
        }

    Raises:
        ValueError
    """

    try:
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.exception("Google OAuth request timed out.")
        raise ValueError("Google authentication timed out.")

    except requests.exceptions.RequestException as exc:
        logger.exception("Google OAuth token exchange failed.")
        raise ValueError("Unable to authenticate with Google.") from exc

    tokens = response.json()

    if "id_token" not in tokens:
        logger.error("Google response missing id_token.")
        raise ValueError("Invalid response received from Google.")

    try:
        idinfo = id_token.verify_oauth2_token(
            tokens["id_token"],
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )

    except google_exceptions.GoogleAuthError as exc:
        logger.exception("Google ID token verification failed.")
        raise ValueError("Invalid Google ID token.") from exc

    email = idinfo.get("email")

    if not email:
        raise ValueError("Google account has no email address.")

    return {
        "email": email,
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture"),
        "email_verified": idinfo.get("email_verified", False),
    }