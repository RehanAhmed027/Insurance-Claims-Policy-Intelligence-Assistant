import json

from langchain_core.tools import tool

from database.queries import get_policy_by_id


@tool
def policy_tool(policy_id: str) -> dict:
    """Retrieve structured policy details using an exact policy ID.

    Returns recorded product name, policy dates, status,
    sum insured, premium, co-pay, deductible and waiting period.
    Coverage clauses must be retrieved from policy documents.
    """
    policy_id = policy_id.strip().upper()

    policy = get_policy_by_id(policy_id)

    if policy is None:
        return {
            "found": False,
            "policy_id": policy_id,
            "message": "Policy not found.",
        }

    return {
        "found": True,
        "source": "SQL:policies",
        "policy": policy,
    }


if __name__ == "__main__":
    result = policy_tool.invoke(
        {"policy_id": "POL243038"}
    )

    print(json.dumps(result, indent=2))