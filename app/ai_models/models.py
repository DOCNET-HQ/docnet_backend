import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AIModel(models.Model):
    class ModelType(models.TextChoices):
        IMAGING = 'imaging', _('Imaging')
        JSON = 'json', _('JSON')
        SIGNAL = 'signal', _('Signal')

    class ModelStatus(models.TextChoices):
        STABLE = 'stable', _('Stable')
        BETA = 'beta', _('Beta')
        RESEARCH = 'research', _('Research')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    version = models.CharField(max_length=50, default='v1.0')
    model_type = models.CharField(
        max_length=20,
        choices=ModelType.choices,
        default=ModelType.IMAGING
    )
    status = models.CharField(
        max_length=20,
        choices=ModelStatus.choices,
        default=ModelStatus.RESEARCH
    )
    tags = models.ManyToManyField(Tag, blank=True)
    icon_name = models.CharField(
        max_length=50, default='Activity', help_text="Lucide icon name"
    )
    image = models.ImageField(upload_to='model_images/', blank=True, null=True)
    model_url = models.URLField(blank=True, null=True)
    docs_url = models.URLField(blank=True, null=True)
    document = models.FileField(upload_to='model_docs/', blank=True, null=True)
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'

    def __str__(self):
        return f"{self.title} ({self.version})"

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return None
