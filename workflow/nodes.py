import json
import re

from rag.claim_analysis import analyze_claim
from rag.document_loader import load_policy_documents
from rag.rag_chain import answer_policy_question

from tools.claims_tool import claims_tool
from tools.customer_tool import customer_tool
from tools.documents_tool import documents_tool
from tools.hospital_tool import hospital_tool
from tools.interactions_tool import interactions_tool
from tools.policy_tool import policy_tool

from workflow.state import AssistantState


def sql_node(state: AssistantState) -> dict:
    entity_type = state["entity_type"]
    entity_id = state["entity_id"]

    results = {}
    warnings = list(state.get("warnings", []))

    if entity_type == "claim":
        claim_result = claims_tool.invoke(
            {"claim_id": entity_id}
        )
        results["claim"] = claim_result

        if claim_result["found"]:
            claim = claim_result["claim"]

            results["customer"] = customer_tool.invoke(
                {"customer_id": claim["customer_id"]}
            )

            if not results["customer"]["found"]:
                warnings.append(
                    "The claim references a customer that was not found."
                )

            results["interactions"] = interactions_tool.invoke(
                {"claim_id": entity_id}
            )

            results["documents"] = documents_tool.invoke(
                {"claim_id": entity_id}
            )

            policy_result = policy_tool.invoke(
                {"policy_id": claim["policy_id"]}
            )
            results["policy"] = policy_result

            if policy_result["found"]:
                policy = policy_result["policy"]

                if policy["customer_id"] != claim["customer_id"]:
                    warnings.append(
                        "Claim and policy customer IDs disagree."
                    )

                if policy["policy_type"] != claim["policy_type"]:
                    warnings.append(
                        "Claim and policy types disagree."
                    )

                start = policy.get("policy_start_date")
                end = policy.get("policy_end_date")
                claim_date = claim.get("claim_date")

                if start and end and claim_date:
                    if not start <= claim_date <= end:
                        warnings.append(
                            "Claim date is outside recorded policy "
                            "dates. Verify renewals and endorsements."
                        )
            else:
                warnings.append(
                    "The claim references a policy that was not found."
                )

            hospital_id = claim.get("hospital_id")

            if hospital_id:
                results["hospital"] = hospital_tool.invoke(
                    {"hospital_id": hospital_id}
                )

                if not results["hospital"]["found"]:
                    warnings.append(
                        "The recorded hospital ID was not found."
                    )

            if str(claim.get("manual_review_flag")).lower() in (
                "1",
                "true",
            ):
                warnings.append(
                    "Manual review is flagged. "
                    "This does not establish fraud."
                )

    elif entity_type == "policy":
        results["policy"] = policy_tool.invoke(
            {"policy_id": entity_id}
        )

    elif entity_type == "hospital":
        results["hospital"] = hospital_tool.invoke(
            {"hospital_id": entity_id}
        )

    elif entity_type == "customer":
        results["customer"] = customer_tool.invoke(
            {"customer_id": entity_id}
        )

    else:
        raise ValueError(
            f"Unsupported entity type: {entity_type}"
        )

    return {
        "sql_results": results,
        "warnings": warnings,
    }


def rag_node(state: AssistantState) -> dict:
    sql_results = state.get("sql_results", {})
    entity_type = state.get("entity_type")

    # Combine SQL facts and policy evidence for claim analysis.
    if state.get("route") == "hybrid" and entity_type == "claim":
        return analyze_claim(
            question=state["question"],
            sql_results=sql_results,
            review_warnings=state.get("warnings", []),
        )

    if entity_type in ("claim", "policy"):
        record = sql_results.get(entity_type, {})

        if not record.get("found"):
            return {
                "answer": record.get(
                    "message",
                    "Requested record was not found."
                ),
                "sources": [],
            }

    products = {
        document.metadata["product_name"]
        for document in load_policy_documents()
    }

    policy_result = sql_results.get("policy", {})

    if policy_result.get("found"):
        product_name = policy_result["policy"]["product_name"]

    elif state.get("route") == "hybrid":
        return {
            "answer": (
                "The linked policy was not found. "
                "Policy analysis cannot be completed."
            ),
            "sources": [],
        }

    else:
        product_name = (
            state.get("product_name") or ""
        ).strip()

        if product_name:
            product_name = next(
                (
                    product
                    for product in products
                    if product.lower() == product_name.lower()
                ),
                product_name,
            )
        else:
            matches = [
                product
                for product in products
                if product.lower() in state["question"].lower()
            ]

            if len(matches) != 1:
                return {
                    "answer": (
                        "Please specify one policy product, "
                        "such as Health Secure Plus."
                    ),
                    "sources": [],
                }

            product_name = matches[0]

    if product_name not in products:
        return {
            "answer": (
                f"No policy document is available for "
                f"'{product_name}'."
            ),
            "sources": [],
        }

    result = answer_policy_question(
        question=state["question"],
        product_name=product_name,
    )

    return {
        "product_name": product_name,
        "answer": result["answer"],
        "sources": result["sources"],
        "warnings": (
            list(state.get("warnings", []))
            + result.get("warnings", [])
        ),
    }


def final_answer_node(state: AssistantState) -> dict:
    route = state["route"]
    warnings = list(state.get("warnings", []))
    sources = state.get("sources", [])

    if route == "clarify":
        return {
            "answer": state["clarification"],
            "sources": [],
            "warnings": warnings,
        }

    if route == "rag":
        return {
            "answer": state.get(
                "answer",
                "The available policy evidence is insufficient."
            ),
            "sources": sources,
            "warnings": warnings,
        }

    results = state.get("sql_results", {})
    parts = []

    # Give a focused answer for a simple claim-status question.
    question = state.get("question", "")

    status_question = bool(
        re.search(r"\bstatus\b", question, re.IGNORECASE)
    )

    asks_for_more = bool(
        re.search(
            r"\b(document|documents|amount|amounts|reason|"
            r"why|policy|hospital|customer|history|"
            r"interaction|interactions|details|summary)\b",
            question,
            re.IGNORECASE,
        )
    )

    if (
        route == "sql"
        and state.get("entity_type") == "claim"
        and status_question
        and not asks_for_more
    ):
        claim_result = results.get("claim", {})

        if not claim_result.get("found"):
            return {
                "answer": claim_result.get(
                    "message",
                    "Claim not found."
                ),
                "sources": [],
                "warnings": warnings,
            }

        claim = claim_result["claim"]

        return {
            "answer": (
                f"Claim {claim['claim_id']} status: "
                f"{claim['claim_status']}. [SQL:claims]"
            ),
            "sources": [],
            "warnings": warnings,
        }

    claim_result = results.get("claim", {})

    if claim_result:
        if not claim_result.get("found"):
            return {
                "answer": claim_result["message"],
                "sources": [],
                "warnings": warnings,
            }

        claim = claim_result["claim"]

        parts.append(
            f"Claim {claim['claim_id']}\n"
            f"Status: {claim['claim_status']}\n"
            f"Claim amount: {claim['claim_amount']}\n"
            f"Approved amount: {claim['approved_amount']}\n"
            f"Recorded reason: "
            f"{claim.get('rejection_or_adjustment_reason') or 'Not supplied'}\n"
            "[SQL:claims]"
        )

    if route == "hybrid" or state.get("entity_type") == "customer":
        customer_result = results.get("customer", {})

        if customer_result:
            if customer_result.get("found"):
                customer = customer_result["customer"]

                parts.append(
                    f"Customer: {customer['customer_id']}\n"
                    f"Name: {customer['customer_name']}\n"
                    f"KYC status: {customer['kyc_status']}\n"
                    f"Risk segment: {customer['risk_segment']}\n"
                    "[SQL:customers]"
                )
            else:
                parts.append(customer_result["message"])

    if route == "hybrid":
        interaction_result = results.get("interactions", {})

        if interaction_result.get("found"):
            interactions = interaction_result["interactions"]

            if interactions:
                interaction_lines = [
                    (
                        f"- {item['interaction_date']} | "
                        f"Channel: {item['channel']} | "
                        f"Intent: {item['intent']} | "
                        f"Sentiment: {item['sentiment']} | "
                        f"Resolution: {item['resolution_status']}"
                    )
                    for item in interactions
                ]

                parts.append(
                    "Recent recorded interactions:\n"
                    + "\n".join(interaction_lines)
                    + "\n[SQL:customer_interactions]"
                )
            else:
                parts.append(
                    "No interaction rows were found for this claim. "
                    "[SQL:customer_interactions]"
                )

            parts.append(interaction_result["note"])

            parts.append(
                "Support resolution status does not determine "
                "the claim outcome."
            )

    document_result = results.get("documents", {})

    if document_result.get("found"):
        parts.append(
            "Recorded document statuses:\n"
            f"- Missing: {len(document_result['missing'])}\n"
            f"- Pending verification: "
            f"{len(document_result['pending_verification'])}\n"
            f"- Rejected: {len(document_result['rejected'])}\n"
            f"- Verified: {len(document_result['verified'])}\n"
            f"- Other statuses: "
            f"{len(document_result['other_statuses'])}\n"
            "[SQL:claim_documents]"
        )

        for label, key in (
            ("Missing documents", "missing"),
            ("Pending verification", "pending_verification"),
            ("Rejected documents", "rejected"),
        ):
            names = [
                document["document_type"]
                for document in document_result[key]
            ]

            if names:
                parts.append(
                    f"{label}: {', '.join(names)}"
                )

        parts.append(document_result["note"])

    policy_result = results.get("policy", {})

    if policy_result:
        if policy_result.get("found"):
            policy = policy_result["policy"]

            parts.append(
                f"Policy: {policy['policy_id']}\n"
                f"Product: {policy['product_name']}\n"
                f"Status: {policy['policy_status']}\n"
                f"Start date: {policy['policy_start_date']}\n"
                f"End date: {policy['policy_end_date']}\n"
                f"Sum insured: {policy['sum_insured']}\n"
                f"Co-pay percentage: {policy['co_pay_pct']}\n"
                f"Deductible: {policy['deductible']}\n"
                f"Recorded waiting period (days): "
                f"{policy['waiting_period_days']}\n"
                "[SQL:policies]"
            )
        else:
            parts.append(policy_result["message"])

    hospital_result = results.get("hospital", {})

    if hospital_result:
        if hospital_result.get("found"):
            hospital = hospital_result["hospital"]

            parts.append(
                f"Hospital: {hospital['hospital_name']}\n"
                f"City: {hospital['city']}\n"
                f"Network status: {hospital['network_status']}\n"
                f"Specialty: {hospital['specialty']}\n"
                "[SQL:hospitals]"
            )
        else:
            parts.append(hospital_result["message"])

    if route == "hybrid":
        parts.append(
            "Evidence-based analysis:\n"
            + state.get(
                "answer",
                "The available policy evidence is insufficient."
            )
        )

        parts.append(
            "Coverage and claim approval cannot be confirmed "
            "without checking applicable conditions and endorsements."
        )

    if warnings:
        parts.append(
            "Review notes:\n"
            + "\n".join(
                f"- {warning}" for warning in warnings
            )
        )

    return {
        "answer": "\n\n".join(parts) or "No records were retrieved.",
        "sources": sources,
        "warnings": warnings,
    }


if __name__ == "__main__":
    # SQL-only status test. No LLM request is made.
    state = {
        "question": "What is the status of CLM300500?",
        "entity_type": "claim",
        "entity_id": "CLM300500",
        "route": "sql",
        "warnings": [],
        "sources": [],
    }

    state.update(sql_node(state))
    result = final_answer_node(state)

    print("Answer:")
    print(result["answer"])

    print("\nReview warnings:")
    print(json.dumps(result["warnings"], indent=2))