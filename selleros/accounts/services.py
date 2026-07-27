import base64
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .google import exchange_code_for_user

from .auth import blacklist_token, create_tokens, refresh_access
from .models import OTPVerification, VerificationChannel

User = get_user_model()


class AuthenticationError(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class OTPError(Exception):
    pass


class OTPDeliveryError(OTPError):
    pass


def _find_user(identifier: str, channel: str):
    identifier = identifier.strip()
    if channel == VerificationChannel.EMAIL:
        return User.objects.filter(email__iexact=identifier).first()
    return User.objects.filter(phone_number=identifier).first()


def _send_phone_otp(phone_number: str, code: str):
    if not all(
        [
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_FROM_NUMBER,
        ]
    ):
        raise OTPDeliveryError(
            "SMS OTP is not configured. Add Twilio credentials or verify by email."
        )

    payload = urllib.parse.urlencode(
        {
            "To": phone_number,
            "From": settings.TWILIO_FROM_NUMBER,
            "Body": f"Your SellerOS verification code is {code}. It expires in {settings.OTP_EXPIRY_MINUTES} minutes.",
        }
    ).encode()
    credentials = base64.b64encode(
        f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()
    ).decode()
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
        data=payload,
        headers={"Authorization": f"Basic {credentials}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status not in (200, 201):
                raise OTPDeliveryError("Could not send SMS OTP.")
    except Exception as exc:
        if isinstance(exc, OTPDeliveryError):
            raise
        raise OTPDeliveryError("Could not send SMS OTP.") from exc


def _send_otp(user, channel: str, code: str):
    if channel == VerificationChannel.EMAIL:
        send_mail(
            subject="Your SellerOS verification code",
            message=(
                f"Your SellerOS verification code is {code}. "
                f"It expires in {settings.OTP_EXPIRY_MINUTES} minutes."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return
    _send_phone_otp(user.phone_number, code)


def _issue_otp(user, channel: str, *, enforce_cooldown: bool = True):
    now = timezone.now()
    if enforce_cooldown:
        latest = OTPVerification.objects.filter(user=user, channel=channel).first()
        if latest and latest.created_at >= now - timedelta(
            seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
        ):
            raise OTPError("Please wait before requesting another OTP.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = OTPVerification.objects.create(
        user=user,
        channel=channel,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    try:
        _send_otp(user, channel, code)
    except Exception:
        otp.delete()
        raise


@transaction.atomic
def register_user(*, full_name: str, email: str, phone_number: str, password: str, verification_channel: str):
    email = email.lower().strip()
    phone_number = phone_number.strip()

    if User.objects.filter(Q(email=email) | Q(phone_number=phone_number)).exists():
        raise UserAlreadyExists("Email or phone number is already registered.")

    user = User.objects.create_user(
        full_name=full_name.strip(),
        email=email,
        phone_number=phone_number,
        password=password,
        is_active=False,
    )
    _issue_otp(user, verification_channel, enforce_cooldown=False)
    return user


@transaction.atomic
def verify_otp(*, identifier: str, channel: str, code: str):
    user = _find_user(identifier, channel)
    if not user:
        raise OTPError("Invalid verification request.")

    otp = (
        OTPVerification.objects.select_for_update()
        .filter(user=user, channel=channel, used_at__isnull=True)
        .first()
    )
    if not otp or otp.expires_at <= timezone.now():
        raise OTPError("OTP has expired. Please request a new one.")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise OTPError("Too many invalid OTP attempts. Please request a new one.")
    if not check_password(code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        raise OTPError("Invalid OTP.")

    otp.used_at = timezone.now()
    otp.save(update_fields=["used_at"])
    if channel == VerificationChannel.EMAIL:
        user.is_email_verified = True
    else:
        user.is_phone_verified = True
    user.is_active = True
    user.save(update_fields=["is_active", "is_email_verified", "is_phone_verified"])
    return {"user": user, "tokens": create_tokens(user)}


def resend_otp(*, identifier: str, channel: str):
    user = _find_user(identifier, channel)
    if not user:
        raise OTPError("Invalid verification request.")
    if user.is_active:
        raise OTPError("This account is already verified.")
    _issue_otp(user, channel)


def login_user(*, username: str, password: str):
    user = authenticate(username=username.strip(), password=password)
    if not user:
        raise AuthenticationError("Invalid email/phone number or password.")
    if not user.is_active:
        raise AuthenticationError("Verify your email or phone number before logging in.")
    return {"user": user, "tokens": create_tokens(user)}


def get_current_user(user):
    if not user:
        raise AuthenticationError("Authentication required.")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "avatar": user.avatar,
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
        "auth_provider": user.auth_provider,
    }


def logout_user(refresh_token: str):
    if not blacklist_token(refresh_token):
        raise AuthenticationError("Invalid Refresh Token")
    return True


def refresh_user_token(refresh_token: str):
    return refresh_access(refresh_token)


def google_login(code: str):

    google_user = exchange_code_for_user(code)

    email = google_user["email"]

    user = User.objects.filter(email=email).first()

    if not user:

        user = User.objects.create_user(
            email=email,
            full_name=google_user["name"],
            phone_number="",
            password=None,
            is_active=True,
            is_email_verified=True,
            avatar=google_user["picture"],
            auth_provider="GOOGLE"

        )

    return {
    "user": {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "avatar": user.avatar,
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
        "auth_provider": user.auth_provider,
    },
    "tokens": create_tokens(user),
}
