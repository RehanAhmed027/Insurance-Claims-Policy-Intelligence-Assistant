from typing import Any, Literal, TypedDict


class AssistantState(TypedDict, total=False):
    # User input
    question: str
    product_name: str

    # Routing decision
    route: Literal["sql", "rag", "hybrid", "clarify"]
    entity_type: Literal[
        "claim",
        "policy",
        "hospital",
        "customer",
    ]
    entity_id: str
    clarification: str

    # Retrieved information
    sql_results: dict[str, Any]
    sources: list[dict[str, Any]]

    # Final output
    answer: str
    warnings: list[str]