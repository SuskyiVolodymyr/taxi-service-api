from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request: Request, *args, **kwargs) -> bool:
        return (request.method in SAFE_METHODS) or (
            request.user and request.user.is_staff
        )
