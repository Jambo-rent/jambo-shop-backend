

from accounts.models import User


class IsShoper():
    message = "You are not the owner of this stock only owners"
    
    def has_permission(self, request, view):
        if request.user.user_type==User.SHOPER:
            return True
        else:
            return False
    
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        return False
