"""
Sign-in with Clerk.

The React app signs the user in with Clerk and sends the session token as
`Authorization: Bearer <token>`. Here we check that token's signature against
Clerk's public keys (JWKS), so the backend never needs the Clerk secret key.

Admins = Clerk user ids listed in ADMIN_USER_IDS (.env).
"""

import time

import jwt
from fastapi import Depends, Header, HTTPException

from . import config

_jwks_client = None


def _client():
    global _jwks_client
    if _jwks_client is None and config.CLERK_JWKS_URL:
        _jwks_client = jwt.PyJWKClient(config.CLERK_JWKS_URL, cache_keys=True)
    return _jwks_client


def verify_token(token):
    """Return the token's claims, or raise HTTPException(401)."""
    client = _client()
    if client is None:
        raise HTTPException(503, "Sign-in is not configured: add VITE_CLERK_PUBLISHABLE_KEY to .env")
    try:
        key = client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], leeway=10,
                            options={"verify_aud": False})
    except jwt.PyJWTError as err:
        raise HTTPException(401, f"Invalid sign-in token: {err}")
    # Clerk puts the frontend address in "azp"; only accept our own frontend
    azp = claims.get("azp")
    if azp and config.CORS_ORIGINS and azp not in config.CORS_ORIGINS:
        raise HTTPException(401, "Token was issued for a different site")
    if claims.get("exp", 0) < time.time() - 10:
        raise HTTPException(401, "Sign-in token expired")
    return claims


def current_user(authorization: str = Header(default="")):
    """FastAPI dependency: the signed-in user, or 401."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Please sign in")
    claims = verify_token(authorization.split(" ", 1)[1].strip())
    user_id = claims["sub"]
    return {"user_id": user_id, "is_admin": user_id in config.ADMIN_USER_IDS}


def admin_user(user=Depends(current_user)):
    if not user["is_admin"]:
        raise HTTPException(403, "Admins only (add your user id to ADMIN_USER_IDS in .env)")
    return user
