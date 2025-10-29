from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()


class PasswordService:
    @staticmethod
    def send_password_setup_email(request, user):
        """
        Send password setup email to new users
        """
        from .email_services import EmailService

        email_service = EmailService()
        email_service.send_password_reset_link(request, user)

    @staticmethod
    def create_user_with_password_setup(email, role=None, **extra_fields):
        """
        Create user with unusable password and send setup email
        """
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'role': role,
                'password': make_password(None),
                **extra_fields
            }
        )

        return user, created
