import uuid
import os


def upload_id_documents(instance, filename):
    """Upload function for ID documents"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/users/profile/id_documents", unique_filename)


def upload_profile_photo(instance, filename):
    """Upload function for ID documents"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/users/profiles/photos", unique_filename)


def upload_cover_image(instance, filename):
    """Upload function for Cover images"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/users/profiles/cover_images", unique_filename)


def upload_doctors_license(instance, filename):
    """Upload function for Doctor's license documents"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/users/profiles/doctors/licenses", unique_filename)


def upload_hospitals_license(instance, filename):
    """Upload function for Hospital's license documents"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/users/profiles/hospitals/licenses", unique_filename)


def upload_specialty_img(instance, filename):
    """Upload function for Specialty images"""
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("media/specialties/images", unique_filename)
