from langchain_core.tools import tool

from database.queries import get_claim_by_id


@tool
def claims_tool(claim_id: str) -> dict:
    """Retrieve recorded claim details using an exact claim ID.

    Use this tool for claim status, amounts, diagnosis or loss type,
    manual review flags, and recorded rejection reasons.
    """
    claim_id = claim_id.strip().upper()

    claim = get_claim_by_id(claim_id)

    if claim is None:
        return {
            "found": False,
            "claim_id": claim_id,
            "message": "Claim not found.",
        }

    return {
        "found": True,
        "source": "SQL:claims",
        "claim": claim,
    }


if __name__ == "__main__":
    result = claims_tool.invoke(
        {"claim_id": "CLM300500"}
    )

    print(result)