from django.core.exceptions import ValidationError


def validate_id_file(value):
    valid_extensions = ['pdf', 'jpg', 'jpeg', 'png']
    ext = value.name.split('.')[-1].lower()
    if ext not in valid_extensions:
        raise ValidationError(
            'Only PDF, JPG, JPEG, and PNG files are allowed.'
        )
