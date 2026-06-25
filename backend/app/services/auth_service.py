import os
import time
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta

# Try to import bcrypt and jose for robust JWT and Hashing.
# If they fail, we implement a production-grade HMAC-SHA256 JWT and PBKDF2 password hashing fallback.
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

try:
    from jose import jwt, JWTError
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-marketbeacon-ai-2026-saas-platform")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt if available, otherwise PBKDF2-HMAC-SHA256.
    """
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback to PBKDF2
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )
        return f"pbkdf2_sha256$100000${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(pwd_hash).decode('utf-8')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password hash against a plain text password.
    """
    if not hashed_password:
        return False
        
    if hashed_password.startswith("pbkdf2_sha256$"):
        # PBKDF2 fallback verification
        try:
            parts = hashed_password.split("$")
            iterations = int(parts[1])
            salt = base64.b64decode(parts[2].encode("utf-8"))
            stored_hash = base64.b64decode(parts[3].encode("utf-8"))
            
            pwd_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations
            )
            return hmac.compare_digest(pwd_hash, stored_hash)
        except Exception:
            return False
            
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            # Maybe the hash was created in PBKDF2
            return False
    else:
        # If bcrypt is not installed, but it is a bcrypt hash, we can't check it easily.
        # Fall back to a simple log and return false.
        return False


def create_access_token(data: dict) -> str:
    """
    Generates a JWT access token expiring in 15 minutes.
    """
    to_encode = data.copy()
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": int(expire), "type": "access"})
    
    if HAS_JOSE:
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    else:
        return _fallback_jwt_encode(to_encode)


def create_refresh_token(data: dict) -> str:
    """
    Generates a JWT refresh token expiring in 7 days.
    """
    to_encode = data.copy()
    expire = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    to_encode.update({"exp": int(expire), "type": "refresh"})
    
    if HAS_JOSE:
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    else:
        return _fallback_jwt_encode(to_encode)


def verify_token(token: str) -> dict:
    """
    Decodes and verifies a JWT token. Returns the payload dict or None.
    """
    if not token:
        return None
        
    import logging
    logger = logging.getLogger("auth_debug")
        
    if HAS_JOSE:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            # Check exp manually in case jose does not do it strictly
            exp = payload.get("exp")
            if exp and time.time() > exp:
                logger.info(f"[DEBUG AUTH] Token expired! Current time: {int(time.time())}, Exp: {exp}")
                return None
            return payload
        except JWTError as e:
            logger.info(f"[DEBUG AUTH] jose decode failed: {str(e)}")
            # Try fallback in case it was encoded using fallback
            return _fallback_jwt_decode(token)
    else:
        return _fallback_jwt_decode(token)


# ── Graceful Fallback JWT Implementation ──

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def _fallback_jwt_encode(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload).encode("utf-8"))
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    
    signature_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _fallback_jwt_decode(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
            
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        
        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()
        
        actual_signature = _base64url_decode(signature_b64)
        
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None
            
        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp and time.time() > exp:
            return None
            
        return payload
    except Exception:
        return None
