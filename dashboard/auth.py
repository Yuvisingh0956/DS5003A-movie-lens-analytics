
"""
Authentication module for MovieLens Analytics.

Responsibilities:
- Authenticate application users.
- Verify passwords using bcrypt.
- Retrieve user roles.
- Create application accounts securely.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import bcrypt

from sqlalchemy import text

from config.database import app_engine


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password):
    """
    Hash a password using bcrypt.

    Returns:
        str: Secure password hash.
    """

    if not password or len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    return password_hash.decode("utf-8")


def verify_password(password, password_hash):
    """
    Verify a password against its stored bcrypt hash.

    Returns:
        bool: True if password matches, otherwise False.
    """

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# USER AUTHENTICATION
# ============================================================

def authenticate_user(username, password):
    """
    Authenticate an application user.

    Returns:
        dict: User information if authentication succeeds.
        None: If username or password is incorrect.
    """

    if not username or not password:
        return None

    query = text("""
        SELECT
            u.user_id,
            u.username,
            u.password_hash,
            u.role_id,
            r.role_name
        FROM app_users u
        JOIN roles r
            ON u.role_id = r.role_id
        WHERE u.username = :username
    """)

    try:
        with app_engine.connect() as connection:
            user = connection.execute(
                query,
                {"username": username.strip()}
            ).mappings().first()

        if user is None:
            return None

        if not verify_password(
            password,
            user["password_hash"]
        ):
            return None

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role_id": user["role_id"],
            "role": user["role_name"]
        }

    except Exception:
        # Do not expose database or authentication details
        # to the login screen.
        return None


# ============================================================
# CREATE APPLICATION USER
# ============================================================

def create_user(username, password, role="user"):
    """
    Create an application account.

    Args:
        username (str): New username.
        password (str): Plain-text password (hashed before storage).
        role (str): Either 'admin' or 'user'.

    Returns:
        tuple: (success, message)
    """

    username = username.strip() if username else ""
    role = role.strip().lower() if role else ""

    if not username:
        return False, "Username cannot be empty."

    if len(username) > 100:
        return False, "Username is too long."

    if role not in ("admin", "user"):
        return False, "Invalid user role."

    try:
        password_hash = hash_password(password)

        with app_engine.begin() as connection:

            existing_user = connection.execute(
                text("""
                    SELECT user_id
                    FROM app_users
                    WHERE username = :username
                """),
                {"username": username}
            ).first()

            if existing_user:
                return False, "Username already exists."

            role_id = connection.execute(
                text("""
                    SELECT role_id
                    FROM roles
                    WHERE role_name = :role
                """),
                {"role": role}
            ).scalar_one_or_none()

            if role_id is None:
                return False, "Requested role does not exist."

            connection.execute(
                text("""
                    INSERT INTO app_users (
                        username,
                        password_hash,
                        role_id
                    )
                    VALUES (
                        :username,
                        :password_hash,
                        :role_id
                    )
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "role_id": role_id
                }
            )

        return True, "User account created successfully."

    except ValueError as error:
        return False, str(error)

    except Exception:
        return False, "Unable to create user account."
