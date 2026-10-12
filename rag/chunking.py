import re

from langchain_core.documents import Document

from rag.document_loader import load_policy_documents


def chunk_policy_documents(documents):
    chunks = []

    for document in documents:
        # Each section starts with a number, such as "4. WAITING PERIOD"
        sections = re.split(
            r"(?m)^\s*(?=\d+\.\s+[A-Z])",
            document.page_content
        )

        for section in sections:
            section = section.strip()

            # Skip the introductory product name and policy type
            if not re.match(r"^\d+\.\s+", section):
                continue

            heading, _, body = section.partition("\n")

            section_number = heading.split(".", 1)[0]

            metadata = {
                **document.metadata,
                "section": heading.strip(),
                "section_number": int(section_number),
                "chunk_id": (
                    f"{document.metadata['source']}:{section_number}"
                ),
            }

            chunks.append(
                Document(
                    page_content=(
                        f"Product: {metadata['product_name']}\n"
                        f"{heading.strip()}\n"
                        f"{body.strip()}"
                    ),
                    metadata=metadata,
                )
            )

    if not chunks:
        raise ValueError("No numbered policy sections were found.")

    return chunks


if __name__ == "__main__":
    documents = load_policy_documents()
    chunks = chunk_policy_documents(documents)

    print(f"Created {len(chunks)} policy chunks.\n")

    example = next(
        chunk
        for chunk in chunks
        if chunk.metadata["product_name"] == "Health Secure Plus"
        and chunk.metadata["section_number"] == 5
    )

    print("Example chunk:")
    print(example.page_content)

    print("\nMetadata:")
    print(example.metadata)