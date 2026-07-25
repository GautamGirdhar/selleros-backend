import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class AuthProvider(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    GOOGLE = "GOOGLE", "Google"


class VerificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.CharField(max_length=150)

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    avatar = models.URLField(blank=True, null=True)

    auth_provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )

    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    is_email_verified = models.BooleanField(default=False)

    is_phone_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        return self.full_name if self.full_name else self.email


class OTPVerification(models.Model):
    """A single-use OTP used to activate a newly registered account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_verifications")
    channel = models.CharField(max_length=10, choices=VerificationChannel.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_verifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "channel", "used_at"])]
