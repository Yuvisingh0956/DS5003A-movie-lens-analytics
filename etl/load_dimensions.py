
import re
import pandas as pd
from sqlalchemy import text

from config.database import engine


RAW_DIR = "data/raw"


def extract_year(title):
    """Extract a four-digit year from the end of a movie title."""
    match = re.search(r"\((\d{4})\)\s*$", str(title))
    return int(match.group(1)) if match else None


def load_dimensions():
    print("Reading source CSV files...")

    movies_df = pd.read_csv(f"{RAW_DIR}/movies.csv")
    links_df = pd.read_csv(f"{RAW_DIR}/links.csv")
    genome_tags_df = pd.read_csv(f"{RAW_DIR}/genome-tags.csv")

    # Prepare movies
    movies = pd.DataFrame({
        "movie_id": movies_df["movieId"],
        "title": movies_df["title"],
        "release_year": movies_df["title"].apply(extract_year)
    })

    # Prepare genres and movie-genre relationships
    genre_pairs = []

    for row in movies_df[["movieId", "genres"]].itertuples(index=False):
        movie_id, genre_string = row

        for genre in str(genre_string).split("|"):
            if genre and genre != "(no genres listed)":
                genre_pairs.append((int(movie_id), genre))

    genre_names = sorted({genre for _, genre in genre_pairs})

    genres = pd.DataFrame({
        "genre_name": genre_names
    })

    # Prepare links; preserve missing TMDb IDs as SQL NULL
    links = pd.DataFrame({
        "movie_id": links_df["movieId"],
        "imdb_id": links_df["imdbId"].astype(str),
        "tmdb_id": links_df["tmdbId"].astype("Int64")
    })

    # Prepare genome tags
    genome_tags = pd.DataFrame({
        "tag_id": genome_tags_df["tagId"],
        "tag_name": genome_tags_df["tag"]
    })

    print("Checking that destination tables are empty...")

    tables = [
        "movies", "genres", "movie_genres",
        "movie_links", "genome_tags"
    ]

    with engine.begin() as conn:
        for table in tables:
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar_one()

            if count > 0:
                raise RuntimeError(
                    f"Table '{table}' is not empty ({count} rows). "
                    "Stopping to avoid duplicate inserts."
                )

        print("Loading movies...")
        movies.to_sql(
            "movies", conn, if_exists="append",
            index=False, chunksize=5000, method="multi"
        )

        print("Loading genres...")
        genres.to_sql(
            "genres", conn, if_exists="append",
            index=False, chunksize=1000, method="multi"
        )

        # Read generated genre IDs from PostgreSQL
        genre_map_df = pd.read_sql(
            text("SELECT genre_id, genre_name FROM genres"),
            conn
        )
        genre_map = dict(zip(
            genre_map_df["genre_name"],
            genre_map_df["genre_id"]
        ))

        movie_genres = pd.DataFrame(
            [
                (movie_id, genre_map[genre])
                for movie_id, genre in genre_pairs
            ],
            columns=["movie_id", "genre_id"]
        ).drop_duplicates()

        print("Loading movie-genre relationships...")
        movie_genres.to_sql(
            "movie_genres", conn, if_exists="append",
            index=False, chunksize=5000, method="multi"
        )

        print("Loading movie links...")
        links.to_sql(
            "movie_links", conn, if_exists="append",
            index=False, chunksize=5000, method="multi"
        )

        print("Loading genome tags...")
        genome_tags.to_sql(
            "genome_tags", conn, if_exists="append",
            index=False, chunksize=1000, method="multi"
        )

    print("\nDimension-table loading completed successfully.")

    print(f"Movies: {len(movies):,}")
    print(f"Genres: {len(genres):,}")
    print(f"Movie-genre relationships: {len(movie_genres):,}")
    print(f"Movie links: {len(links):,}")
    print(f"Genome tags: {len(genome_tags):,}")


if __name__ == "__main__":
    load_dimensions()
