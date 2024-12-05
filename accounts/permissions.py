from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.exceptions import InvalidToken
from accounts.models import JWTTokenBlacklist


class BaseAuthPermission(BasePermission):
    message = "Staff users are not allowed to access this service"
    
    def has_permission(self, request, view):
        try:
            if bool(request.user and request.user.is_authenticated and not request.user.admin):
                token = request.META["HTTP_AUTHORIZATION"].split(" ")[-1]
                JWTTokenBlacklist.objects.get(token=token, user=request.user)
                raise InvalidToken()
            return False
        except JWTTokenBlacklist.DoesNotExist:
            return bool(request.user and request.user.is_authenticated and not request.user.admin)
    
    def has_object_permission(self, request, view, obj):
        try:
            if bool(request.user and request.user.is_authenticated and not request.user.admin):
                token = request.META["HTTP_AUTHORIZATION"].split(" ")[-1]
                JWTTokenBlacklist.objects.get(token=token, user=request.user)
                raise InvalidToken()
            return False
        except JWTTokenBlacklist.DoesNotExist:
            return bool(request.user and request.user.is_authenticated and not request.user.admin)