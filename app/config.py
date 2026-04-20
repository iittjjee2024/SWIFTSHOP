import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set in .env file!\n"
        "Add this to your .env:\n"
        "DATABASE_URL=postgresql://postgres:9000@localhost/swiftshop_db"
    )
if "sqlite" in DATABASE_URL.lower():
    raise ValueError(
        "SQLite is not allowed! Use PostgreSQL only.\n"
        "Update DATABASE_URL in .env to:\n"
        "DATABASE_URL=postgresql://postgres:9000@localhost/swiftshop_db"
    )

JWT_SECRET = os.getenv("JWT_SECRET", "replace-me-securely")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
