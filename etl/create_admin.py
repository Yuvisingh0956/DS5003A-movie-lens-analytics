
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import getpass
import bcrypt

from sqlalchemy import text
from config.database import engine


def create_admin():
    username = input("Enter admin username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass.getpass("Enter admin password: ")
    confirm = getpass.getpass("Confirm admin password: ")

    if password != confirm:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    with engine.begin() as connection:

        existing = connection.execute(
            text("""
                SELECT user_id
                FROM app_users
                WHERE username = :username
            """),
            {"username": username}
        ).first()

        if existing:
            print("This username already exists.")
            return

        connection.execute(
            text("""
                INSERT INTO app_users
                    (username, password_hash, role_id)
                VALUES
                    (:username, :password_hash, 1)
            """),
            {
                "username": username,
                "password_hash": password_hash
            }
        )

    print("\nAdministrator account created successfully!")


if __name__ == "__main__":
    create_admin()
