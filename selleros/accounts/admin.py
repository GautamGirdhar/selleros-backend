from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    ordering = ("-date_joined",)

    list_display = (
        "email",
        "full_name",
        "auth_provider",
        "is_email_verified",
        "is_phone_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )

    search_fields = (
        "email",
        "full_name",
    )

    readonly_fields = (
        "id",
        "date_joined",
        "updated_at",
        "last_login",
    )

    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "id",
                    "email",
                    "password",
                    "full_name",
                    "avatar",
                    "google_id",
                    "auth_provider",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "is_phone_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "full_name",
                ),
            },
        ),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )
