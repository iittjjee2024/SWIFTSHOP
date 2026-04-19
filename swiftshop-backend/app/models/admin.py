
from app.database import create_tables, SessionLocal
from app.models import User
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
        print(f"  Admin already exists: {ADMIN_EMAIL}")
        db.close()
        return

    admin = User(
        email      = ADMIN_EMAIL,
        password   = hash_password(ADMIN_PASSWORD),
        first_name = ADMIN_FNAME,
        last_name  = ADMIN_LNAME,
        is_admin   = True,
        is_active  = True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()

    print(" Admin user created successfully!")
    print(f"   Email    : {ADMIN_EMAIL}")
    print(f"   Password : {ADMIN_PASSWORD}")
    print(f"   Role     : Admin")
    print()
    print(" Login at: POST /api/v1/users/login")
    print("   Change the password after first login!")

if __name__ == "__main__":
    create_admin()
    
