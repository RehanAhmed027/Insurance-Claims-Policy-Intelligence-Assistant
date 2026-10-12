import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from rag.vector_store import get_vector_store
from rag.document_loader import load_policy_documents
from rag.chunking import chunk_policy_documents


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


@lru_cache(maxsize=1)
def get_policy_chunks():
    documents = load_policy_documents()
    return chunk_policy_documents(documents)


@lru_cache(maxsize=1)
def get_search_store():
    return get_vector_store()


@lru_cache(maxsize=20)
def get_product_keyword_index(product_name):
    # Filter before keyword ranking
    chunks = [
        chunk
        for chunk in get_policy_chunks()
        if chunk.metadata["product_name"] == product_name
    ]

    if not chunks:
        raise ValueError(
            f"No policy chunks found for: {product_name}"
        )

    tokenized_chunks = [
        tokenize(chunk.page_content)
        for chunk in chunks
    ]

    return chunks, BM25Okapi(tokenized_chunks)


def hybrid_search(question, product_name, k=6):
    if k < 1:
        raise ValueError("k must be at least 1.")

    chunks, keyword_index = get_product_keyword_index(
        product_name
    )

    # Retrieve a larger candidate set before merging
    candidate_count = min(12, len(chunks))

    vector_results = get_search_store().similarity_search(
        query=question,
        k=candidate_count,
        filter={"product_name": product_name},
    )

    keyword_scores = keyword_index.get_scores(
        tokenize(question)
    )

    keyword_positions = sorted(
        range(len(chunks)),
        key=lambda index: keyword_scores[index],
        reverse=True,
    )

    keyword_results = [
        chunks[index]
        for index in keyword_positions
        if keyword_scores[index] > 0
    ][:candidate_count]

    # Reciprocal Rank Fusion combines ranking positions,
    # rather than comparing incompatible raw scores.
    combined_scores = {}
    documents_by_id = {}

    for results in (vector_results, keyword_results):
        for rank, document in enumerate(results, start=1):
            chunk_id = document.metadata["chunk_id"]

            documents_by_id[chunk_id] = document

            combined_scores[chunk_id] = (
                combined_scores.get(chunk_id, 0.0)
                + 1.0 / (60 + rank)
            )

    ranked_ids = sorted(
        combined_scores,
        key=combined_scores.get,
        reverse=True,
    )

    return [
        documents_by_id[chunk_id]
        for chunk_id in ranked_ids[:k]
    ]


if __name__ == "__main__":
    results = hybrid_search(
        question="What is the maternity waiting period?",
        product_name="Health Secure Plus",
        k=4,
    )

    for number, document in enumerate(results, start=1):
        print(f"\nResult {number}")
        print(document.page_content)
        print(f"Source: {document.metadata['source']}")