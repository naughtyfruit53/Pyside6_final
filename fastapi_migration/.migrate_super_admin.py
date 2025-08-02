from app.core.database import SessionLocal
from app.models.base import User, PlatformUser

db = SessionLocal()
try:
    admin_email = "naughtyfruit53@gmail.com"
    user = db.query(User).filter(User.email == admin_email).first()
    if user:
        platform_user = PlatformUser(
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            role="super_admin",
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        db.add(platform_user)
        db.delete(user)
        db.commit()
        print("Super admin migrated to PlatformUser successfully.")
    else:
        print("No super admin user found in User table.")
finally:
    db.close()