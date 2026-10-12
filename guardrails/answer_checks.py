import re


def check_answer_citations(answer: str, sources: list) -> list[str]:
    warnings = []

    allowed_ids = {
        source["evidence_id"]
        for source in sources
    }

    cited_ids = set(
        re.findall(r"\[([^\[\]\n]+)\]", answer)
    )

    unknown_ids = cited_ids - allowed_ids

    if unknown_ids:
        warnings.append(
            "Unrecognized citations: "
            + ", ".join(sorted(unknown_ids))
        )

    is_abstention = (
        "the available policy evidence is insufficient"
        in answer.lower()
    )

    if sources and not cited_ids and not is_abstention:
        warnings.append(
            "The policy answer has no evidence citations."
        )

    if not sources and not is_abstention:
        warnings.append(
            "No policy evidence was supplied for this answer."
        )

    return warnings