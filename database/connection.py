
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from config import DATABASE_PATH

# Ensure the database folder exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Build the SQLite connection URL
DATABASE_URL = URL.create(
    drivername="sqlite",
    database=str(DATABASE_PATH)
)

# Create a reusable database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
