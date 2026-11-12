
import json
import re
from pathlib import Path
from collections import Counter

import pandas as pd


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "raw"
REPORT_DIR = ROOT_DIR / "data" / "processed"

CHUNK_SIZE = 250_000

VALID_GENRES = {
    "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "IMAX", "Musical", "Mystery", "Romance",
    "Sci-Fi", "Thriller", "War", "Western",
    "(no genres listed)"
}

report = {}


def add_result(name, result):
    report[name] = result


# --------------------------------------------------
# LOAD SMALL REFERENCE DATASETS
# --------------------------------------------------

def load_reference_data():

    movies = pd.read_csv(DATA_DIR / "movies.csv")
    genome_tags = pd.read_csv(DATA_DIR / "genome-tags.csv")

    movie_ids = set(movies["movieId"].dropna().astype(int))
    tag_ids = set(genome_tags["tagId"].dropna().astype(int))

    return movies, genome_tags, movie_ids, tag_ids


# --------------------------------------------------
# SMALL FILE VALIDATION
# --------------------------------------------------

def validate_movies(movies):

    years = []

    for title in movies["title"].astype(str):
        match = re.search(r"\((\d{4})\)\s*$", title)

        if match:
            years.append(int(match.group(1)))

    genres = set()

    for value in movies["genres"].dropna():
        genres.update(value.split("|"))

    result = {
        "rows": len(movies),
        "duplicate_movie_ids": int(
            movies["movieId"].duplicated().sum()
        ),
        "missing_movie_ids": int(
            movies["movieId"].isna().sum()
        ),
        "missing_titles": int(
            movies["title"].isna().sum()
        ),
        "missing_genres": int(
            movies["genres"].isna().sum()
        ),
        "invalid_genres": sorted(
            genres - VALID_GENRES
        ),
        "movies_with_extracted_year": len(years),
        "movies_without_extracted_year": len(movies) - len(years)
    }

    add_result("movies", result)


def validate_genome_tags(genome_tags):

    result = {
        "rows": len(genome_tags),
        "duplicate_tag_ids": int(
            genome_tags["tagId"].duplicated().sum()
        ),
        "duplicate_tag_names": int(
            genome_tags["tag"].duplicated().sum()
        ),
        "missing_tag_ids": int(
            genome_tags["tagId"].isna().sum()
        ),
        "missing_tag_names": int(
            genome_tags["tag"].isna().sum()
        )
    }

    add_result("genome_tags", result)


def validate_links(movie_ids):

    path = DATA_DIR / "links.csv"
    df = pd.read_csv(path)

    result = {
        "rows": len(df),
        "duplicate_movie_ids": int(
            df["movieId"].duplicated().sum()
        ),
        "missing_tmdb_ids": int(
            df["tmdbId"].isna().sum()
        ),
        "missing_imdb_ids": int(
            df["imdbId"].isna().sum()
        ),
        "unknown_movie_ids": int(
            (~df["movieId"].isin(movie_ids)).sum()
        )
    }

    add_result("links", result)


# --------------------------------------------------
# CHUNKED GENOME VALIDATION
# --------------------------------------------------

def validate_genome_scores(movie_ids, tag_ids):

    path = DATA_DIR / "genome-scores.csv"

    movie_counts = Counter()

    total_rows = 0
    missing_values = 0
    invalid_relevance = 0
    unknown_movies = 0
    unknown_tags = 0

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        missing_values += int(
            chunk.isna().sum().sum()
        )

        invalid_relevance += int(
            (
                (chunk["relevance"] < 0) |
                (chunk["relevance"] > 1)
            ).sum()
        )

        unknown_movies += int(
            (~chunk["movieId"].isin(movie_ids)).sum()
        )

        unknown_tags += int(
            (~chunk["tagId"].isin(tag_ids)).sum()
        )

        counts = chunk["movieId"].value_counts()

        for movie_id, count in counts.items():
            movie_counts[int(movie_id)] += int(count)

    expected_tags = len(tag_ids)

    incorrect_counts = {
        movie_id: count
        for movie_id, count in movie_counts.items()
        if count != expected_tags
    }

    result = {
        "total_rows": total_rows,
        "distinct_movies": len(movie_counts),
        "distinct_tags_expected": expected_tags,
        "missing_values": missing_values,
        "invalid_relevance_scores": invalid_relevance,
        "unknown_movie_references": unknown_movies,
        "unknown_tag_references": unknown_tags,
        "movies_with_incomplete_or_excess_scores": len(
            incorrect_counts
        ),
        "expected_rows_if_dense": (
            len(movie_counts) * expected_tags
        ),
        "composite_duplicate_check": (
            "Deferred to PostgreSQL staging validation"
        )
    }

    add_result("genome_scores", result)


# --------------------------------------------------
# CHUNKED USER TAG VALIDATION
# --------------------------------------------------


def validate_user_tags(movie_ids):

    path = DATA_DIR / "tags.csv"

    total_rows = 0
    missing_tags = 0
    missing_values = 0
    unknown_movies = 0
    unique_users = set()

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE,
        keep_default_na=False
    ):

        total_rows += len(chunk)

        # Count genuinely empty tag values only.
        # Literal strings "NA", "Na", and "null" are valid tags.
        missing_tags += int(
            chunk["tag"].isna().sum()
            + chunk["tag"].astype(str).str.strip().eq("").sum()
        )

        # Count genuinely empty fields across all columns.
        missing_values += int(
            chunk.replace(
                r"^\s*$", pd.NA, regex=True
            ).isna().sum().sum()
        )

        unknown_movies += int(
            (~chunk["movieId"].isin(movie_ids)).sum()
        )

        unique_users.update(
            chunk["userId"].dropna().astype(int).unique()
        )

    result = {
        "total_rows": total_rows,
        "missing_tags": missing_tags,
        "missing_values": missing_values,
        "unknown_movie_references": unknown_movies,
        "distinct_users": len(unique_users)
    }

    add_result("user_tags", result)


# --------------------------------------------------
# CHUNKED RATINGS VALIDATION
# --------------------------------------------------

def validate_ratings(movie_ids):

    path = DATA_DIR / "ratings.csv"

    total_rows = 0
    missing_values = 0
    invalid_ratings = 0
    invalid_timestamps = 0
    unknown_movies = 0

    unique_users = set()
    rating_counts = Counter()

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        missing_values += int(
            chunk.isna().sum().sum()
        )

        rating = chunk["rating"]

        invalid_ratings += int(
            (
                (rating < 0.5) |
                (rating > 5.0) |
                ((rating * 2) % 1 != 0)
            ).sum()
        )

        invalid_timestamps += int(
            (
                chunk["timestamp"] < 0
            ).sum()
        )

        unknown_movies += int(
            (~chunk["movieId"].isin(movie_ids)).sum()
        )

        unique_users.update(
            chunk["userId"].dropna().astype(int).unique()
        )

        rating_counts.update(
            chunk["rating"].value_counts().to_dict()
        )

    result = {
        "total_rows": total_rows,
        "missing_values": missing_values,
        "invalid_ratings": invalid_ratings,
        "invalid_timestamps": invalid_timestamps,
        "unknown_movie_references": unknown_movies,
        "distinct_users": len(unique_users),
        "rating_value_counts": {
            str(k): int(v)
            for k, v in sorted(rating_counts.items())
        },
        "user_movie_duplicate_check": (
            "Deferred to PostgreSQL staging validation"
        )
    }

    add_result("ratings", result)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nMOVIELENS DATA VALIDATION")
    print("=" * 60)

    movies, genome_tags, movie_ids, tag_ids = (
        load_reference_data()
    )

    print("\n[1/6] Validating movies...")
    validate_movies(movies)

    print("[2/6] Validating genome tags...")
    validate_genome_tags(genome_tags)

    print("[3/6] Validating links...")
    validate_links(movie_ids)

    print("[4/6] Validating genome scores...")
    validate_genome_scores(movie_ids, tag_ids)

    print("[5/6] Validating user tags...")
    validate_user_tags(movie_ids)

    print("[6/6] Validating ratings...")
    validate_ratings(movie_ids)

    output_file = REPORT_DIR / "validation_report.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETED")
    print("=" * 60)

    print(f"\nReport saved to: {output_file}")

    for name, result in report.items():
        print(f"\n{name.upper()}")

        for key, value in result.items():
            if isinstance(value, dict):
                continue

            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
