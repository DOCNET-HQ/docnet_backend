from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from hospitals.models import Hospital
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class ReviewBase(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="%(class)s_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def is_updated(self):
        return self.updated_at > self.created_at + timezone.timedelta(seconds=60)

    def __str__(self):
        return f"{self.user.email} - {self.rating} stars"


class DoctorReview(ReviewBase):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="reviews")

    class Meta:
        unique_together = ["user", "doctor"]
        verbose_name = "Doctor Review"
        verbose_name_plural = "Doctor Reviews"


class HospitalReview(ReviewBase):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, related_name="reviews"
    )

    class Meta:
        unique_together = ["user", "hospital"]
        verbose_name = "Hospital Review"
        verbose_name_plural = "Hospital Reviews"
