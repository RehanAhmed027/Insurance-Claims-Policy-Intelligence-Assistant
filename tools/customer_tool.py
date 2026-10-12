import json

from langchain_core.tools import tool
from database.queries import get_customer_by_id


@tool
def customer_tool(customer_id: str) -> dict:
    """Retrieve recorded customer details using an exact customer ID."""
    customer_id = customer_id.strip().upper()
    customer = get_customer_by_id(customer_id)

    if customer is None:
        return {
            "found": False,
            "customer_id": customer_id,
            "message": "Customer not found.",
        }

    return {
        "found": True,
        "source": "SQL:customers",
        "customer": customer,
    }


if __name__ == "__main__":
    result = customer_tool.invoke(
        {"customer_id": "CUST147306"}
    )
    print(json.dumps(result, indent=2))