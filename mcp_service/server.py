from mcp.server.fastmcp import FastMCP

from tools.claims_tool import claims_tool
from tools.customer_tool import customer_tool
from tools.documents_tool import documents_tool
from tools.hospital_tool import hospital_tool
from tools.interactions_tool import interactions_tool
from tools.policy_tool import policy_tool


mcp = FastMCP("Insurance Intelligence")


@mcp.tool()
def lookup_claim(claim_id: str) -> dict:
    """Retrieve recorded claim details using an exact claim ID."""
    return claims_tool.invoke({"claim_id": claim_id})


@mcp.tool()
def lookup_documents(claim_id: str) -> dict:
    """Retrieve recorded document statuses for a claim.

    These statuses do not certify required-document completeness.
    """
    return documents_tool.invoke({"claim_id": claim_id})


@mcp.tool()
def lookup_policy(policy_id: str) -> dict:
    """Retrieve a policy schedule using an exact policy ID."""
    return policy_tool.invoke({"policy_id": policy_id})


@mcp.tool()
def lookup_hospital(hospital_id: str) -> dict:
    """Retrieve hospital details and recorded network status."""
    return hospital_tool.invoke({"hospital_id": hospital_id})


@mcp.tool()
def lookup_customer(customer_id: str) -> dict:
    """Retrieve a synthetic customer profile by exact customer ID."""
    return customer_tool.invoke({"customer_id": customer_id})


@mcp.tool()
def lookup_interactions(claim_id: str) -> dict:
    """Retrieve up to ten recent recorded interactions for a claim."""
    return interactions_tool.invoke({"claim_id": claim_id})


if __name__ == "__main__":
    mcp.run(transport="stdio")