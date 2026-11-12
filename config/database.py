
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()


def build_database_url(user, password):
    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )


# Administrative connection: retain this for ETL scripts.
DATABASE_URL = build_database_url(
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Restricted connection: use this in the Streamlit dashboard.
APP_DATABASE_URL = build_database_url(
    os.getenv("APP_DB_USER"),
    os.getenv("APP_DB_PASSWORD"),
)

app_engine = create_engine(
    APP_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


def test_connection():
    for name, db_engine in [
        ("Administrative", engine),
        ("Application", app_engine),
    ]:
        try:
            with db_engine.connect() as connection:
                result = connection.execute(
                    text("SELECT current_user, version();")
                ).first()

                print(f"{name} database connection successful!")
                print("Connected as:", result[0])

        except Exception as error:
            print(f"{name} database connection failed:", error)


if __name__ == "__main__":
    test_connection()
