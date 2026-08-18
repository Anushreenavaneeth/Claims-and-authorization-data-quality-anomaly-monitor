"""
Development seed script — creates admin and worker users.
WARNING: These credentials are for LOCAL DEVELOPMENT ONLY.
Remove or rotate before any production deployment.

Usage:
    python seed.py
"""

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password
from app.utils.enums import UserRole

SEED_USERS = [
    {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "Admin1234!",
        "role": UserRole.ADMIN,
    },
    {
        "name": "Worker User",
        "email": "worker@example.com",
        "password": "Worker1234!",
        "role": UserRole.WORKER,
    },
]


def seed():
    db = SessionLocal()
    try:
        for data in SEED_USERS:
            existing = db.query(User).filter(User.email == data["email"]).first()
            if existing:
                print(f"  [skip] {data['email']} already exists")
                continue
            user = User(
                name=data["name"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
                is_active=True,
            )
            db.add(user)
            print(f"  [created] {data['email']} ({data['role']})")
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
