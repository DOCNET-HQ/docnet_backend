from rest_framework.permissions import BasePermission


class IsAdminOrCreateOnly(BasePermission):
    message = "You must be an admin to view this list"

    def has_permission(self, request, view):
        return request.method in ["POST"] or request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    message = "You must be the owner of this instance or an admin to perform this action."  # noqa

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsOwnerOrAdminOrReadOnly(BasePermission):
    message = (
        "You must be the owner of this instance or an admin to modify this content. "  # noqa
        "Read-only access is allowed for everyone."
    )

    def has_object_permission(self, request, view, obj):
        return request.method in ["GET", "HEAD", "OPTIONS"] or (
            request.user.is_staff or obj.user == request.user
        )


class IsAdminOrReadOnly(BasePermission):
    message = "You must be an admin to modify this content. Read-only access is allowed for everyone."  # noqa

    def has_permission(self, request, view):
        return request.method in ["GET", "HEAD", "OPTIONS"] or request.user.is_staff


class IsHospital(BasePermission):
    message = "You must be associated with a hospital to perform this action."

    def has_permission(self, request, view):
        return request.user.role == "hospital" and hasattr(
            request.user, "hospital_profile"
        )


class IsDoctor(BasePermission):
    message = "You must be associated with a doctor to perform this action."

    def has_permission(self, request, view):
        return request.user.role == "doctor" and hasattr(request.user, "doctor_profile")


class IsPatient(BasePermission):
    message = "You must be associated with a patient to perform this action."

    def has_permission(self, request, view):
        return request.user.role == "patient" and hasattr(
            request.user, "patient_profile"
        )
