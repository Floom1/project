from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """Allow access only to users with one of the given roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def manager_required(view_func):
    """Allow access to HR, Director and Admin roles."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_manage:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def analytics_required(view_func):
    """Allow access to Director and Admin roles only."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_view_analytics:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
