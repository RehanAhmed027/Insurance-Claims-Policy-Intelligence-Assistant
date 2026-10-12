from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Dataset folders
DATA_DIR = BASE_DIR / "data"
CSV_DIR = DATA_DIR / "csv_files"
POLICY_DIR = DATA_DIR / "policy_documents"

# Structured data storage
DATABASE_PATH = BASE_DIR / "database" / "insurance.db"

# Policy embedding storage
CHROMA_DIR = BASE_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = "insurance_policy_documents"

# Models
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"