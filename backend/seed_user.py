"""
Seed script to create a test user for local development

Usage:
    python seed_user.py
"""
from app.core.database import SessionLocal
from app.repositories.user import UserRepository
from app.core.auth import hash_password

def create_seed_user():
    """Create a test user for local development"""
    db = SessionLocal()
    user_repo = UserRepository(db)

    # Test user credentials
    test_email = "test@example.com"
    test_password = "password123"
    test_name = "Test User"
    test_domain = "example.com"

    try:
        # Check if user already exists
        if user_repo.email_exists(test_email):
            print(f"✓ User {test_email} already exists")
            return

        # Create user
        user_data = {
            "name": test_name,
            "email": test_email,
            "password_hash": hash_password(test_password),
            "domain": test_domain
        }

        user = user_repo.create(user_data)

        print(f"✓ Created seed user:")
        print(f"  Email: {user.email}")
        print(f"  Password: {test_password}")
        print(f"  Name: {user.name}")
        print(f"  ID: {user.id}")

    except Exception as e:
        print(f"✗ Error creating seed user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_seed_user()
