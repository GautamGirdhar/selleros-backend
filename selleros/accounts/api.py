from ninja import Router
from ninja.errors import HttpError
from .auth import get_authenticated_user
from .services import get_current_user


from .schemas import (
    RegisterSchema,
    LoginSchema,
    VerifyOtpSchema,
    ResendOtpSchema,
    AuthResponseSchema,
    MessageSchema,
    OtpSentSchema,
    LogoutSchema,
    GoogleAuthSchema,
)

from .services import (
    register_user,
    login_user,
    logout_user,
    refresh_user_token,
    verify_otp,
    resend_otp,
    AuthenticationError,
    UserAlreadyExists,
    OTPError,
    OTPDeliveryError,
    google_login,
    get_current_user,
)

router = Router(tags=["Authentication"])


@router.post("/register", response=OtpSentSchema)
def register(request, payload: RegisterSchema):
    try:
        register_user(
            full_name=payload.full_name,
            email=payload.email,
            phone_number=payload.phone_number,
            password=payload.password,
            verification_channel=payload.verification_channel,
        )

        return {
            "success": True,
            "message": "OTP sent. Verify it to activate your account.",
            "verification_channel": payload.verification_channel,
        }

    except UserAlreadyExists as e:
        raise HttpError(400, str(e))

    except AuthenticationError as e:
        raise HttpError(400, str(e))

    except OTPDeliveryError as e:
        raise HttpError(503, str(e))


@router.post("/verify-otp", response=AuthResponseSchema)
def verify_signup_otp(request, payload: VerifyOtpSchema):
    try:
        return verify_otp(
            identifier=payload.identifier,
            channel=payload.verification_channel,
            code=payload.code,
        )
    except OTPError as e:
        raise HttpError(400, str(e))


@router.post("/resend-otp", response=OtpSentSchema)
def resend_signup_otp(request, payload: ResendOtpSchema):
    try:
        resend_otp(
            identifier=payload.identifier,
            channel=payload.verification_channel,
        )
        return {
            "success": True,
            "message": "OTP sent.",
            "verification_channel": payload.verification_channel,
        }
    except OTPDeliveryError as e:
        raise HttpError(503, str(e))
    except OTPError as e:
        raise HttpError(400, str(e))


@router.post("/login", response=AuthResponseSchema)
def login(request, payload: LoginSchema):
    try:
        result = login_user(
            username=payload.username,   # Email OR Phone
            password=payload.password,
        )

        return {
            "user": result["user"],
            "tokens": result["tokens"],
        }

    except AuthenticationError as e:
        raise HttpError(401, str(e))


@router.post("/logout", response=MessageSchema)
def logout(request, payload: LogoutSchema):
    try:
        logout_user(payload.refresh_token)

        return {
            "success": True,
            "message": "Logout successful."
        }

    except AuthenticationError as e:
        raise HttpError(400, str(e))

@router.post("/refresh")
def refresh(request, refresh_token: str):
    try:
        return refresh_user_token(refresh_token)

    except AuthenticationError as e:
        raise HttpError(401, str(e))

@router.post("/google", response=AuthResponseSchema)
def google_auth(request, payload: GoogleAuthSchema):
    return google_login(payload.code)

@router.get("/me")
def me(request):
    auth_header = request.headers.get("Authorization")

    user = get_authenticated_user(auth_header)

    if not user:
        raise HttpError(401, "Authentication required.")

    return get_current_user(user)