from langchain_core.tools import tool

from database.queries import (
    get_claim_by_id,
    get_claim_documents,
)


@tool
def documents_tool(claim_id: str) -> dict:
    """Retrieve recorded document statuses for an exact claim ID.

    Distinguishes missing uploads, pending verification,
    rejected documents, and verified documents.
    Does not certify that every required document is present.
    """
    claim_id = claim_id.strip().upper()

    if get_claim_by_id(claim_id) is None:
        return {
            "found": False,
            "claim_id": claim_id,
            "message": "Claim not found.",
        }

    documents = get_claim_documents(claim_id)

    missing = []
    pending = []
    rejected = []
    verified = []
    other = []

    for document in documents:
        upload = str(
            document.get("upload_status") or ""
        ).strip().lower()

        verification = str(
            document.get("verification_status") or ""
        ).strip().lower()

        if upload == "missing":
            missing.append(document)
        elif verification == "rejected":
            rejected.append(document)
        elif verification == "pending":
            pending.append(document)
        elif upload == "uploaded" and verification == "verified":
            verified.append(document)
        else:
            other.append(document)

    return {
        "found": True,
        "claim_id": claim_id,
        "source": "SQL:claim_documents",
        "total_records": len(documents),
        "missing": missing,
        "pending_verification": pending,
        "rejected": rejected,
        "verified": verified,
        "other_statuses": other,
        "note": (
            "These are recorded document statuses. "
            "Required-document completeness cannot be confirmed "
            "from this table alone."
        ),
    }


if __name__ == "__main__":
    import json

    result = documents_tool.invoke(
        {"claim_id": "CLM300500"}
    )

    print(json.dumps(result, indent=2))