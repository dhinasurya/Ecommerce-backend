from functools import wraps
from flask import request, jsonify
from utils.jwt_utils import decode_jwt


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Missing token"}), 401

        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user_id = payload["user_id"]
        return f(*args, **kwargs)

    return wrapper
