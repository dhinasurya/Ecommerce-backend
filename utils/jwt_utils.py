import jwt
from datetime import datetime, timedelta
from flask import current_app


def create_access_token(user_id):
    """Create a short-lived access token (15 minutes)."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def create_refresh_token(user_id):
    """Create a long-lived refresh token (7 days)."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        current_app.config.get("REFRESH_SECRET_KEY")
        or current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )


def decode_access_token(token):
    """
    Decode and validate access token.
    Returns: dict with payload on success
    Raises: jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure
    """
    try:
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        # Verify token type
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise


def decode_refresh_token(token):
    """
    Decode and validate refresh token.
    Returns: dict with payload on success
    Raises: jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure
    """
    try:
        secret = (
            current_app.config.get("REFRESH_SECRET_KEY")
            or current_app.config["SECRET_KEY"]
        )
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        # Verify token type
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise


def decode_jwt(token):
    """Legacy function for backward compatibility. Use decode_access_token instead."""
    try:
        return decode_access_token(token)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
