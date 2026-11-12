
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

FILES = {
    "movies": "movies.csv",
    "genome_tags": "genome-tags.csv",
    "genome_scores": "genome-scores.csv",
    "links": "links.csv",
    "tags": "tags.csv",
    "ratings": "ratings.csv"
}


def profile_file(name, filename):

    file_path = DATA_DIR / filename

    print("\n" + "=" * 65)
    print(f"DATASET: {name.upper()}")
    print("=" * 65)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    try:
        df = pd.read_csv(file_path)

        print("\nShape:")
        print(df.shape)

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nData types:")
        print(df.dtypes)

        print("\nMissing values:")
        print(df.isnull().sum())

        print("\nDuplicate rows:")
        print(df.duplicated().sum())

        print("\nSample records:")
        print(df.head(5).to_string(index=False))

        print("\nMemory usage:")
        print(
            round(
                df.memory_usage(deep=True).sum()
                / (1024 ** 2),
                2
            ),
            "MB"
        )

    except Exception as error:
        print(f"Error profiling {name}: {error}")


def main():

    print("\nMOVIELENS DATASET PROFILING")
    print("=" * 65)

    for name, filename in FILES.items():
        profile_file(name, filename)

    print("\nDATASET PROFILING COMPLETED")


if __name__ == "__main__":
    main()
