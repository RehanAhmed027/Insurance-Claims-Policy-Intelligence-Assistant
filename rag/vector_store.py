from langchain_chroma import Chroma

from config import CHROMA_DIR, CHROMA_COLLECTION_NAME
from rag.document_loader import load_policy_documents
from rag.chunking import chunk_policy_documents
from rag.embeddings import get_embedding_model


def get_vector_store():
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embedding_model(),
    )


def store_policy_documents():
    documents = load_policy_documents()
    chunks = chunk_policy_documents(documents)

    vector_store = get_vector_store()

    # Stable IDs prevent duplicate entries when rerunning
    chunk_ids = [
        chunk.metadata["chunk_id"]
        for chunk in chunks
    ]

    vector_store.add_documents(
        documents=chunks,
        ids=chunk_ids,
    )

    print(f"Stored {len(chunks)} policy chunks in ChromaDB.")
    print(f"Storage folder: {CHROMA_DIR}")

    return vector_store


if __name__ == "__main__":
    vector_store = store_policy_documents()

    results = vector_store.similarity_search(
        query="What is the maternity waiting period?",
        k=3,
        filter={"product_name": "Health Secure Plus"},
    )

    print("\nRetrieved policy sections:\n")

    for number, document in enumerate(results, start=1):
        print(f"Result {number}")
        print(document.page_content)
        print(f"Source: {document.metadata['source']}")
        print(f"Section: {document.metadata['section']}")
        print()
        