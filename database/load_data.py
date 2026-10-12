import pandas as pd

from config import CSV_DIR
from database.connection import engine


# Business CSV files and their SQL table names
TABLE_FILES = {
    "customers": "customers.csv",
    "policies": "policies.csv",
    "claims": "claims.csv",
    "claim_documents": "claim_documents.csv",
    "hospitals": "hospitals.csv",
    "customer_interactions": "customer_interactions.csv",
}


def load_csv_data():
    # Check all files before starting
    missing_files = [
        filename
        for filename in TABLE_FILES.values()
        if not (CSV_DIR / filename).is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Missing CSV files in {CSV_DIR}: {missing_files}"
        )

    for table_name, filename in TABLE_FILES.items():
        file_path = CSV_DIR / filename
        total_rows = 0

        print(f"Loading {filename}...")

        # One transaction for each table
        with engine.begin() as connection:
            for chunk_number, chunk in enumerate(
                pd.read_csv(file_path, chunksize=50_000)
            ):
                # Replace the table on the first chunk.
                # Append the remaining chunks.
                chunk.to_sql(
                    name=table_name,
                    con=connection,
                    if_exists="replace" if chunk_number == 0 else "append",
                    index=False,
                    chunksize=1_000,
                )

                total_rows += len(chunk)

        print(f"Loaded {total_rows:,} rows into '{table_name}'.")

    print("\nAll six business tables loaded successfully!")


if __name__ == "__main__":
    load_csv_data()