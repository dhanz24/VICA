from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.config.database import Base, engine, get_session, get_db

# Create the database tables
Base.metadata.create_all(bind=engine)

def test_database_connection():
    # Test koneksi ke database
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
            print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")



# def test_create_user():
#     # Test creating a user
#     db: Session = next(get_session())
#     try:
#         new_user = User(name="Test User", email="test@example.com")
#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user)
#         assert new_user.id is not None
#         print("User creation successful.")
#     except Exception as e:
#         print(f"User creation failed: {e}")
#     finally:
#         db.close()

if __name__ == "__main__":
    test_database_connection()
    # test_create_user()