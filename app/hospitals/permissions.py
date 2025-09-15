from rest_framework import permissions


class IsOwnerOrAdminReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Admins have read-only access to all objects.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for admins
        if request.method in permissions.SAFE_METHODS and request.user.is_staff:
            return True

        # Write permissions are only allowed to the owner of the hospital
        return obj.user == request.user


class IsHospitalOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class for hospital-related objects.
    Hospital owners can access their own data, admins can access all.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_staff:
            return True

        # Hospital owners can access their own hospital data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'hospital'):
            return obj.hospital.user == request.user

        return False


class IsAdminOrHospitalOwnerReadOnly(permissions.BasePermission):
    """
    Permission that allows:
    - Admins: Full CRUD access
    - Hospital owners: Read-only access to their own data
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_staff:
            return True

        # Hospital owners have read-only access to their own data
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            elif hasattr(obj, 'hospital'):
                return obj.hospital.user == request.user

        return False


class IsVerifiedHospital(permissions.BasePermission):
    """
    Permission that only allows verified hospitals to perform certain actions.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Check if user has a verified hospital profile
        try:
            hospital = request.user.hospital_profile
            return hospital.kyc_status == 'APPROVED' and hospital.is_active
        except:
            return False
