from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


if __name__ == "__main__":
    embedding_model = get_embedding_model()

    vector = embedding_model.embed_query(
        "What is the maternity waiting period?"
    )

    print("Embedding model loaded successfully.")
    print(f"Vector dimensions: {len(vector)}")
    print(f"First five values: {vector[:5]}")