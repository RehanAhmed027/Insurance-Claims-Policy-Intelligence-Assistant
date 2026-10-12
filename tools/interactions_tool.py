import json

from langchain_core.tools import tool

from database.queries import (
    get_claim_by_id,
    get_claim_interactions,
)


@tool
def interactions_tool(claim_id: str) -> dict:
    """Retrieve up to ten most recent interactions for a claim.

    Interaction intent, sentiment and resolution status describe
    support history; they do not establish the claim outcome.
    """
    claim_id = claim_id.strip().upper()

    if get_claim_by_id(claim_id) is None:
        return {
            "found": False,
            "claim_id": claim_id,
            "message": "Claim not found.",
        }

    interactions = get_claim_interactions(claim_id)

    return {
        "found": True,
        "claim_id": claim_id,
        "source": "SQL:customer_interactions",
        "returned_count": len(interactions),
        "interactions": interactions,
        "note": (
            "At most ten recent interactions are returned. "
            "No rows does not prove that no contact occurred."
        ),
    }


if __name__ == "__main__":
    result = interactions_tool.invoke(
        {"claim_id": "CLM300500"}
    )

    print(json.dumps(result, indent=2))