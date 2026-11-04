from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def role_required(*roles):
    """Decorator to enforce that current_user has at least one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            user_roles = [r.name for r in current_user.roles]
            # Super Admin has omnipotent access
            if 'Super Admin' in user_roles:
                return f(*args, **kwargs)
                
            has_valid_role = any(r in user_roles for r in roles)
            if not has_valid_role:
                flash(f"Access Denied: Requires one of these roles: {', '.join(roles)}", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_code):
    """Decorator to enforce granular permission code."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(permission_code):
                flash(f"Access Denied: You do not possess the required permission: {permission_code}", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
