import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from config import BASE_DIR
from guardrails.answer_checks import check_answer_citations
from prompts.templates import POLICY_QA_PROMPT
from rag.hybrid_search import hybrid_search
from rag.reranker import rerank_documents


@lru_cache(maxsize=1)
def get_answer_chain():
    # Load the API key from the main project's .env file
    load_dotenv(BASE_DIR / ".env", override=True)

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "Add OPENAI_API_KEY to your project's .env file."
        )

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0,
        timeout=60,
        max_retries=2,
    )

    return POLICY_QA_PROMPT | llm | StrOutputParser()


def answer_policy_question(question, product_name):
    # Retrieve candidates using vector and keyword search
    candidates = hybrid_search(
        question=question,
        product_name=product_name,
        k=10,
    )

    # Keep the three highest-ranked sections
    documents = rerank_documents(
        question=question,
        documents=candidates,
        top_k=3,
    )

    if not documents:
        return {
            "answer": "The available policy evidence is insufficient.",
            "sources": [],
            "warnings": [],
        }

    # Attach evidence IDs for the model to cite
    context = "\n\n".join(
        f"[{document.metadata['chunk_id']}]\n"
        f"{document.page_content}"
        for document in documents
    )

    # Generate an answer from the retrieved evidence
    answer = get_answer_chain().invoke(
        {
            "question": question,
            "product_name": product_name,
            "context": context,
        }
    )

    # Return the evidence alongside the answer
    sources = [
        {
            "evidence_id": document.metadata["chunk_id"],
            "source": document.metadata["source"],
            "section": document.metadata["section"],
            "text": document.page_content,
        }
        for document in documents
    ]

    # Flag missing or unrecognized citation IDs
    warnings = check_answer_citations(answer, sources)

    return {
        "answer": answer,
        "sources": sources,
        "warnings": warnings,
    }


if __name__ == "__main__":
    result = answer_policy_question(
        question="What is the maternity waiting period?",
        product_name="Health Secure Plus",
    )

    print("\nAnswer:")
    print(result["answer"])

    print("\nRetrieved sources:")
    for source in result["sources"]:
        print(
            f"- [{source['evidence_id']}] "
            f"{source['section']}"
        )

    print("\nCitation warnings:")
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"- {warning}")
    else:
        print("No citation-format issues detected.")