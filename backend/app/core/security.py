import os
from datetime import datetime, timedelta
import jwt
import bcrypt

# Import the centralized configuration
from core.config import settings

def hash_password(password: str) -> str:
    """Generates a secure, salted cryptographic hash from a plain password string."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password input against its stored database hash verification string."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=8)) -> str:
    """Mints a statelessly verifiable JWT signature containing tenant and scope identifiers."""
    payload = data.copy()
    expire = datetime.utcnow() + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Validates and parses a token signature payload, throwing an exception if signature is invalid."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return {}