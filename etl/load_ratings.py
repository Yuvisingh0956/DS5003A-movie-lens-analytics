
from pathlib import Path

from config.database import engine


CSV_PATH = Path("data/raw/ratings.csv")


def load_ratings():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"File not found: {CSV_PATH}")

    connection = engine.raw_connection()
    cursor = connection.cursor()

    try:
        # Check that neither table already contains imported data.
        cursor.execute("SELECT COUNT(*) FROM ratings_staging")
        staging_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ratings")
        final_count = cursor.fetchone()[0]

        if staging_count > 0 or final_count > 0:
            raise RuntimeError(
                f"Import stopped: ratings_staging has {staging_count:,} "
                f"rows and ratings has {final_count:,} rows. "
                "Inspect the tables before retrying."
            )

        # Step 1: Bulk-load the CSV into staging.
        print("Starting ratings CSV bulk import...")
        print(f"Source: {CSV_PATH}")
        print("This may take several minutes.")

        copy_sql = """
            COPY ratings_staging
                (user_id, movie_id, rating, rating_timestamp)
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE)
        """

        with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            cursor.copy_expert(copy_sql, csv_file)

        cursor.execute("SELECT COUNT(*) FROM ratings_staging")
        staging_count = cursor.fetchone()[0]

        connection.commit()

        print(f"\nStaging import completed: {staging_count:,} rows")

        # Step 2: Check for duplicate user/movie pairs.
        print("Checking for duplicate user-movie pairs...")

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT user_id, movie_id
                FROM ratings_staging
                GROUP BY user_id, movie_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """)

        duplicate_pairs = cursor.fetchone()[0]

        if duplicate_pairs > 0:
            cursor.execute("""
                SELECT user_id, movie_id, COUNT(*) AS occurrences
                FROM ratings_staging
                GROUP BY user_id, movie_id
                HAVING COUNT(*) > 1
                ORDER BY occurrences DESC
                LIMIT 10
            """)

            examples = cursor.fetchall()

            print(f"\nFound {duplicate_pairs:,} duplicate user-movie pairs.")
            print("Example duplicate pairs:")
            for row in examples:
                print(row)

            print(
                "\nFinal ratings table was not populated. "
                "Staging data has been retained for investigation."
            )
            return

        print("No duplicate user-movie pairs found.")

        # Step 3: Insert into the final table.
        print("Inserting records into final ratings table...")

        cursor.execute("""
            INSERT INTO ratings (
                user_id,
                movie_id,
                rating,
                rating_timestamp
            )
            SELECT
                user_id,
                movie_id,
                rating,
                rating_timestamp
            FROM ratings_staging
        """)

        inserted_count = cursor.rowcount
        connection.commit()

        print("\nRatings loaded successfully!")
        print(f"Staging rows: {staging_count:,}")
        print(f"Final rows inserted: {inserted_count:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    load_ratings()
