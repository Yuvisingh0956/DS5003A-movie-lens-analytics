
from pathlib import Path

from config.database import engine


CSV_PATH = Path("data/raw/genome-scores.csv")


def load_genome_scores():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"File not found: {CSV_PATH}")

    connection = engine.raw_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM genome_scores")
        existing_rows = cursor.fetchone()[0]

        if existing_rows > 0:
            raise RuntimeError(
                f"genome_scores already contains {existing_rows:,} rows. "
                "Stopping to avoid duplicate loading."
            )

        print("Starting PostgreSQL bulk import...")
        print(f"Source: {CSV_PATH}")
        print("This may take several minutes.")

        copy_sql = """
            COPY genome_scores (movie_id, tag_id, relevance)
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE)
        """

        with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            cursor.copy_expert(copy_sql, csv_file)

        cursor.execute("SELECT COUNT(*) FROM genome_scores")
        loaded_rows = cursor.fetchone()[0]

        connection.commit()

        print("\nGenome scores loaded successfully!")
        print(f"Rows loaded: {loaded_rows:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    load_genome_scores()
