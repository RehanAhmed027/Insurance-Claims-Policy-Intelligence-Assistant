import json

from langchain_core.tools import tool

from database.queries import get_hospital_by_id


@tool
def hospital_tool(hospital_id: str) -> dict:
    """Retrieve hospital details and recorded network status.

    Requires an exact hospital ID. Network membership alone
    does not guarantee cashless authorization or claim approval.
    """
    hospital_id = hospital_id.strip().upper()

    hospital = get_hospital_by_id(hospital_id)

    if hospital is None:
        return {
            "found": False,
            "hospital_id": hospital_id,
            "message": "Hospital not found.",
        }

    return {
        "found": True,
        "source": "SQL:hospitals",
        "hospital": hospital,
    }


if __name__ == "__main__":
    result = hospital_tool.invoke(
        {"hospital_id": "HOSP1000"}
    )

    print(json.dumps(result, indent=2))