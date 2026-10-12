import re

from workflow.state import AssistantState


def route_question(state: AssistantState) -> dict:
    question = state.get("question", "").strip()

    if not question:
        return {
            "route": "clarify",
            "clarification": "Please enter an insurance question.",
        }

    # Extract unique identifiers while preserving their order.
    identifiers = list(
        dict.fromkeys(
            re.findall(
                r"\b(?:CLM|POL|HOSP|CUST)\d+\b",
                question.upper(),
            )
        )
    )

    if len(identifiers) > 1:
        return {
            "route": "clarify",
            "clarification": (
                "Please ask about one claim, policy, "
                "hospital, or customer ID at a time."
            ),
        }

    if identifiers:
        entity_id = identifiers[0]

        if entity_id.startswith("CLM"):
            entity_type = "claim"
        elif entity_id.startswith("POL"):
            entity_type = "policy"
        elif entity_id.startswith("CUST"):
            entity_type = "customer"
        else:
            entity_type = "hospital"

        # Claim/policy analysis needs records and policy evidence.
        needs_policy_evidence = bool(
            re.search(
                r"\b(analy[sz]e|analysis|summari[sz]e|summary|"
                r"covered|coverage|cover|eligible|eligibility|"
                r"waiting|exclusions?|cashless|reimbursement)\b",
                question,
                re.IGNORECASE,
            )
        )

        route = (
            "hybrid"
            if entity_type in ("claim", "policy")
            and needs_policy_evidence
            else "sql"
        )

        return {
            "route": route,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    # Personal record questions require an identifier.
    needs_identifier = bool(
        re.search(
            r"\bmy\s+(?:claim|policy|documents|hospital)\b|"
            r"\bclaim\s+status\b|"
            r"\bstatus\s+of\s+(?:the\s+)?claim\b|"
            r"\bcustomer\s+(?:profile|details|information)\b",
            question,
            re.IGNORECASE,
        )
    )

    # General claim procedures belong to policy retrieval.
    general_policy_question = bool(
        re.search(
            r"\b(?:claim|claims)\s+(?:procedure|process|rules)\b|"
            r"\bhow\s+(?:do|can|should)\s+i\s+"
            r"(?:file|submit|make)\s+(?:a\s+)?claim\b|"
            r"\bdocuments\s+(?:are\s+)?required\b",
            question,
            re.IGNORECASE,
        )
    )

    if needs_identifier and not general_policy_question:
        return {
            "route": "clarify",
            "clarification": (
                "Please provide the relevant claim, policy, "
                "hospital, or customer ID."
            ),
        }

    # Policy wording is retrieved from documents.
    # The RAG node asks for a product when one cannot be identified.
    return {"route": "rag"}


if __name__ == "__main__":
    examples = [
        "What is the status of CLM300500?",
        "Which documents are missing for CLM300500?",
        "Analyze claim CLM300500.",
        "Is HOSP1000 in the network?",
        "Show customer CUST147306.",
        "What is the maternity waiting period under Health Secure Plus?",
        "What is my claim status?",
        "How do I submit a claim under Health Secure Plus?",
        "What documents are required for a claim under Family Care Gold?",
    ]

    for question in examples:
        print(f"\nQuestion: {question}")
        print(route_question({"question": question}))