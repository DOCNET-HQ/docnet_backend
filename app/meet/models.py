import uuid
from django.db import models
from meet.utils import generate_meet_id
from django.contrib.auth import get_user_model

User = get_user_model()


class Meet(models.Model):
    id = models.CharField(
        max_length=12, unique=True, primary_key=True, default=generate_meet_id
    )
    # Host can be null for meets without a specific host (Like appointments)
    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="hosted_meets",
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(User, related_name="meets")
    channel_name = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Meet - ({self.id})"
