from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = claims.get("roles", [])
            
            if not any(role in user_roles for role in roles):
                return jsonify({"msg": "Permission denied"}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def handle_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR in {fn.__name__}: {error_msg}")
            return jsonify({"error": error_msg, "status": "failed"}), 500
    return wrapper
