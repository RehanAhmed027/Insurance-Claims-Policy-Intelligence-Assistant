import re


BLOCKED_PATTERNS = [
    r"\bignore\s+(?:all\s+)?(?:previous|system)\s+instructions\b",
    r"\breveal\s+(?:the\s+|your\s+)?system\s+prompt\b",
    r"\bdrop\s+table\b",
    r"\bdelete\s+from\b",
]


def validate_question(question: str) -> str:
    if not isinstance(question, str):
        raise ValueError("Question must be text.")

    question = question.strip()

    if len(question) < 3:
        raise ValueError(
            "Please enter a question of at least 3 characters."
        )

    if len(question) > 2000:
        raise ValueError(
            "Please keep your question within 2,000 characters."
        )

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            raise ValueError(
                "Please ask an insurance question without "
                "instructions to override the assistant or modify data."
            )

    return question


if __name__ == "__main__":
    print(validate_question(
        "  What is the status of CLM300500?  "
    ))