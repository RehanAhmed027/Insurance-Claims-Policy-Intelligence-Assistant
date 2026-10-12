from functools import lru_cache

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL
from rag.hybrid_search import hybrid_search


@lru_cache(maxsize=1)
def get_reranker():
    return CrossEncoder(
        RERANKER_MODEL,
        device="cpu",
    )


def rerank_documents(question, documents, top_k=3):
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not documents:
        return []

    pairs = [
        (question, document.page_content)
        for document in documents
    ]

    scores = get_reranker().predict(pairs)

    ranked_results = sorted(
        zip(documents, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    # Create copies so cached document metadata stays unchanged
    return [
        Document(
            page_content=document.page_content,
            metadata={
                **document.metadata,
                "rerank_score": float(score),
            },
        )
        for document, score in ranked_results[:top_k]
    ]


if __name__ == "__main__":
    question = "What is the maternity waiting period?"

    candidates = hybrid_search(
        question=question,
        product_name="Health Secure Plus",
        k=10,
    )

    results = rerank_documents(
        question=question,
        documents=candidates,
        top_k=3,
    )

    for number, document in enumerate(results, start=1):
        print(f"\nResult {number}")
        print(document.page_content)
        print(f"Source: {document.metadata['source']}")
        print(
            f"Rerank score: "
            f"{document.metadata['rerank_score']:.4f}"
        )