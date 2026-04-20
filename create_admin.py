"""
Run this script once to create the default admin user.
Usage: python create_admin.py
"""

from app.database import create_tables, SessionLocal
from app.models import User
from app.models.admin import Admin
from app.services.auth import hash_password
from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL    = "admin@swiftshop.com"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_FNAME    = "Swift"
ADMIN_LNAME    = "Admin"

def create_admin():
    create_tables()
    db = SessionLocal()

    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print(f"⚠️  Admin already exists: {ADMIN_EMAIL}")
        db.close()
        return

    # Create user
    user = User(
        email      = ADMIN_EMAIL,
        password   = hash_password(ADMIN_PASSWORD),
        first_name = ADMIN_FNAME,
        last_name  = ADMIN_LNAME,
        is_admin   = True,
        is_active  = True,
    )
    db.add(user)
    db.flush()  # get user.id before commit

    # Create admin profile in admins table
    admin = Admin(
        user_id     = user.id,
        admin_level = 2,          # super admin
        department  = "Management",
        notes       = "Default super admin created at setup",
        is_active   = True,
    )
    db.add(admin)
    db.commit()
    db.refresh(user)

    print("✅ Admin user created successfully!")
    print(f"   Email      : {ADMIN_EMAIL}")
    print(f"   Password   : {ADMIN_PASSWORD}")
    print(f"   Admin Level: 2 (Super Admin)")
    print(f"   Department : Management")
    print()
    print("👉 Login at : POST /api/v1/users/login")
    print("📋 Admins   : GET  /api/v1/admin/admins")
    print("⚠️  Change the password after first login!")
    db.close()

if __name__ == "__main__":
    create_admin()

