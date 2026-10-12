from langgraph.graph import StateGraph, START, END

from workflow.state import AssistantState
from guardrails.input_checks import validate_question
from workflow.router import route_question
from workflow.nodes import (
    sql_node,
    rag_node,
    final_answer_node,
)


def choose_first_node(state: AssistantState) -> str:
    return {
        "sql": "sql",
        "hybrid": "sql",
        "rag": "rag",
        "clarify": "final_answer",
    }[state["route"]]


def choose_after_sql(state: AssistantState) -> str:
    if state["route"] == "hybrid":
        return "rag"

    return "final_answer"


def build_graph():
    builder = StateGraph(AssistantState)

    builder.add_node("router", route_question)
    builder.add_node("sql", sql_node)
    builder.add_node("rag", rag_node)
    builder.add_node("final_answer", final_answer_node)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        choose_first_node,
        {
            "sql": "sql",
            "rag": "rag",
            "final_answer": "final_answer",
        },
    )

    builder.add_conditional_edges(
        "sql",
        choose_after_sql,
        {
            "rag": "rag",
            "final_answer": "final_answer",
        },
    )

    builder.add_edge("rag", "final_answer")
    builder.add_edge("final_answer", END)

    return builder.compile()


assistant_graph = build_graph()


def ask_assistant(question: str, product_name: str = ""):
    try:
        question = validate_question(question)
    except ValueError as error:
        return {
            "route": "clarify",
            "answer": str(error),
            "sources": [],
            "warnings": [],
        }

    return assistant_graph.invoke(
        {
            "question": question,
            "product_name": product_name,
            "warnings": [],
            "sources": [],
        }
    )


if __name__ == "__main__":
    result = ask_assistant(
        "What is the status of CLM300500?"
    )

    print(f"Route: {result['route']}")
    print(f"\nAnswer:\n{result['answer']}")