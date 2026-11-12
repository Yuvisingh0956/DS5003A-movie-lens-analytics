
from pathlib import Path

from config.database import engine


CSV_PATH = Path("data/raw/tags.csv")


def load_user_tags():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"File not found: {CSV_PATH}")

    connection = engine.raw_connection()
    cursor = connection.cursor()

    try:
        # Prevent accidental duplicate imports.
        cursor.execute("SELECT COUNT(*) FROM user_tags")
        existing_valid = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'user_tags_rejected'
        """)
        rejected_table_exists = cursor.fetchone()[0] > 0

        existing_rejected = 0
        if rejected_table_exists:
            cursor.execute("SELECT COUNT(*) FROM user_tags_rejected")
            existing_rejected = cursor.fetchone()[0]

        if existing_valid > 0 or existing_rejected > 0:
            raise RuntimeError(
                "User tags already appear to have been loaded. "
                "Inspect user_tags and user_tags_rejected before retrying."
            )

        # Persistent table for records that cannot enter user_tags.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_tags_rejected (
                rejected_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id INTEGER,
                movie_id INTEGER,
                tag TEXT,
                tag_timestamp BIGINT,
                rejection_reason TEXT NOT NULL
            )
        """)

        # Temporary staging table accepts missing tag values.
        cursor.execute("""
            CREATE TEMP TABLE user_tags_staging (
                user_id INTEGER,
                movie_id INTEGER,
                tag TEXT,
                tag_timestamp BIGINT
            ) ON COMMIT DROP
        """)

        print("Starting user-tags bulk import...")
        print(f"Source: {CSV_PATH}")

        copy_sql = """
            COPY user_tags_staging
                (user_id, movie_id, tag, tag_timestamp)
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE)
        """

        with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            cursor.copy_expert(copy_sql, csv_file)

        cursor.execute("SELECT COUNT(*) FROM user_tags_staging")
        total_rows = cursor.fetchone()[0]

        # Keep records with non-empty tag text.
        cursor.execute("""
            INSERT INTO user_tags (
                user_id, movie_id, tag, tag_timestamp
            )
            SELECT
                user_id, movie_id, tag, tag_timestamp
            FROM user_tags_staging
            WHERE tag IS NOT NULL
              AND BTRIM(tag) <> ''
        """)
        valid_rows = cursor.rowcount

        # Preserve rejected records and explain why they were rejected.
        cursor.execute("""
            INSERT INTO user_tags_rejected (
                user_id, movie_id, tag, tag_timestamp, rejection_reason
            )
            SELECT
                user_id,
                movie_id,
                tag,
                tag_timestamp,
                CASE
                    WHEN tag IS NULL THEN 'Missing tag'
                    WHEN BTRIM(tag) = '' THEN 'Empty tag'
                END
            FROM user_tags_staging
            WHERE tag IS NULL
               OR BTRIM(tag) = ''
        """)
        rejected_rows = cursor.rowcount

        connection.commit()

        print("\nUser-tags loading completed successfully.")
        print(f"Source rows: {total_rows:,}")
        print(f"Valid tags loaded: {valid_rows:,}")
        print(f"Rejected tags preserved: {rejected_rows:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    load_user_tags()
