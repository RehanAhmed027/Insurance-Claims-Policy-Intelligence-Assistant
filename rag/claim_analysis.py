import json
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from config import BASE_DIR
from guardrails.answer_checks import check_answer_citations
from prompts.templates import CLAIM_ANALYSIS_PROMPT
from rag.hybrid_search import hybrid_search
from rag.reranker import rerank_documents


@lru_cache(maxsize=1)
def get_claim_analysis_chain():
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

    return CLAIM_ANALYSIS_PROMPT | llm | StrOutputParser()


def build_sql_context(sql_results):
    """Select relevant facts without sending the customer profile."""
    context = {}

    claim_result = sql_results.get("claim", {})

    if claim_result.get("found"):
        claim = claim_result["claim"]

        context["SQL:claims"] = {
            key: claim.get(key)
            for key in (
                "claim_id",
                "policy_id",
                "policy_type",
                "claim_date",
                "claim_amount",
                "claim_status",
                "approved_amount",
                "diagnosis_or_loss_type",
                "fraud_risk_score",
                "manual_review_flag",
                "rejection_or_adjustment_reason",
            )
        }

    policy_result = sql_results.get("policy", {})

    if policy_result.get("found"):
        policy = policy_result["policy"]

        context["SQL:policies"] = {
            key: policy.get(key)
            for key in (
                "policy_id",
                "product_name",
                "policy_type",
                "policy_start_date",
                "policy_end_date",
                "policy_status",
                "sum_insured",
                "co_pay_pct",
                "deductible",
                "waiting_period_days",
            )
        }

    document_result = sql_results.get("documents", {})

    if document_result.get("found"):
        document_context = {
            "total_records": document_result["total_records"],
            "note": document_result["note"],
        }

        for status in (
            "missing",
            "pending_verification",
            "rejected",
            "verified",
            "other_statuses",
        ):
            document_context[status] = [
                {
                    "document_type": document["document_type"],
                    "upload_status": document["upload_status"],
                    "verification_status": document["verification_status"],
                }
                for document in document_result[status]
            ]

        context["SQL:claim_documents"] = document_context

    hospital_result = sql_results.get("hospital", {})

    if hospital_result.get("found"):
        hospital = hospital_result["hospital"]

        context["SQL:hospitals"] = {
            key: hospital.get(key)
            for key in (
                "hospital_name",
                "city",
                "network_status",
                "specialty",
            )
        }

    interaction_result = sql_results.get("interactions", {})

    if interaction_result.get("found"):
        context["SQL:customer_interactions"] = {
            "note": interaction_result["note"],
            "interactions": [
                {
                    key: interaction.get(key)
                    for key in (
                        "interaction_date",
                        "channel",
                        "intent",
                        "sentiment",
                        "resolution_status",
                    )
                }
                for interaction in interaction_result["interactions"]
            ],
        }

    return context


def analyze_claim(question, sql_results, review_warnings):
    claim_result = sql_results.get("claim", {})
    policy_result = sql_results.get("policy", {})

    if not claim_result.get("found"):
        return {
            "answer": "Claim not found.",
            "sources": [],
            "warnings": list(review_warnings),
        }

    if not policy_result.get("found"):
        return {
            "answer": (
                "The linked policy was not found. "
                "Policy analysis cannot be completed."
            ),
            "sources": [],
            "warnings": list(review_warnings),
        }

    claim = claim_result["claim"]
    product_name = policy_result["policy"]["product_name"]

    # Include the recorded loss/diagnosis to improve retrieval
    # for broad questions such as "Analyze this claim".
    retrieval_question = (
        f"{question}\n"
        f"Diagnosis or loss: "
        f"{claim.get('diagnosis_or_loss_type') or 'Not recorded'}.\n"
        "Relevant coverage, exclusions, waiting periods, "
        "claim procedure and documentation."
    )

    candidates = hybrid_search(
        question=retrieval_question,
        product_name=product_name,
        k=12,
    )

    documents = rerank_documents(
        question=retrieval_question,
        documents=candidates,
        top_k=6,
    )

    if not documents:
        return {
            "answer": "The available policy evidence is insufficient.",
            "sources": [],
            "warnings": list(review_warnings),
        }

    sources = [
        {
            "evidence_id": document.metadata["chunk_id"],
            "source": document.metadata["source"],
            "section": document.metadata["section"],
            "text": document.page_content,
        }
        for document in documents
    ]

    policy_context = "\n\n".join(
        f"[{source['evidence_id']}]\n{source['text']}"
        for source in sources
    )

    sql_context = build_sql_context(sql_results)

    answer = get_claim_analysis_chain().invoke(
        {
            "question": question,
            "sql_context": json.dumps(
                sql_context,
                ensure_ascii=False,
                indent=2,
            ),
            "policy_context": policy_context,
            "review_warnings": json.dumps(
                review_warnings,
                ensure_ascii=False,
            ),
        }
    )

    # Allow citations to the SQL labels actually supplied,
    # as well as the retrieved policy section IDs.
    citation_sources = sources + [
        {"evidence_id": label}
        for label in sql_context
    ]

    warnings = list(review_warnings)
    warnings.extend(
        check_answer_citations(answer, citation_sources)
    )

    return {
        "answer": answer,
        "sources": sources,
        "warnings": warnings,
    }


if __name__ == "__main__":
    # Verify context preparation without calling OpenAI.
    from workflow.nodes import sql_node

    state = {
        "question": "Analyze claim CLM300500.",
        "entity_type": "claim",
        "entity_id": "CLM300500",
        "route": "hybrid",
        "warnings": [],
    }

    result = sql_node(state)
    context = build_sql_context(result["sql_results"])

    print("Selected SQL facts for claim analysis:")
    print(json.dumps(context, ensure_ascii=False, indent=2))

    print("\nReview warnings:")
    print(result["warnings"])