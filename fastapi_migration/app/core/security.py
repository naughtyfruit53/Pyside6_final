from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt, exceptions
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], 
    organization_id: Optional[int] = None,
    expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "organization_id": organization_id
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_token(token: str) -> tuple[Union[str, None], Union[int, None], Union[str, None]]:
    """Verify token and return email, organization_id, and user_type"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        organization_id = payload.get("organization_id")
        user_type = payload.get("user_type", "organization")  # Default to organization for backward compatibility
        return email, organization_id, user_type
    except exceptions.JWTError:
        return None, None, None

def check_password_strength(password: str) -> tuple[bool, str]:
    """Check password strength and return validation result"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def is_super_admin_email(email: str) -> bool:
    """Check if email belongs to a super admin"""
    super_admin_emails = getattr(settings, 'SUPER_ADMIN_EMAILS', [])
    return email.lower() in [e.lower() for e in super_admin_emails]