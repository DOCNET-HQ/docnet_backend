import uuid
from django.db import models
from users.choices import USER_ROLES
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """
    Custom UserManager model that manages User model
    """

    use_in_migrations = True

    def create_user(self, email, password, **extra_fields):
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(
                {"email": f"Input a valid Email: {email} is not valid"}
            )

        user = self.model(email=self.normalize_email(email), **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.role = "admin"
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, validators=[validate_email])

    role = models.CharField(max_length=50, choices=USER_ROLES, default="patient")

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            self.email = self.email.lower()
        except Exception as e:
            raise e

        super(User, self).save(*args, **kwargs)

    @property
    def profile(self):
        profile_attr = f"{self.role}_profile"
        return getattr(self, profile_attr, None)

    @property
    def name(self):
        return self.get_name()

    def get_name(self):
        """Return the user's name"""
        if self.profile:
            return self.profile.name
        else:
            return self.email

    def __str__(self):
        """String representation of a user"""
        return f"{self.email} ({self.role})"

    class Meta:
        ordering = ("-date_joined",)
