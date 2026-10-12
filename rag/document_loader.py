from langchain_core.documents import Document

from config import POLICY_DIR


def load_policy_documents():
    if not POLICY_DIR.is_dir():
        raise FileNotFoundError(
            f"Policy folder not found: {POLICY_DIR}"
        )

    documents = []

    for file_path in sorted(POLICY_DIR.glob("*.txt")):
        content = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            raise ValueError(
                f"Policy document is empty: {file_path.name}"
            )

        lines = content.splitlines()
        product_name = lines[0].strip()

        policy_type = next(
            (
                line.split(":", 1)[1].strip()
                for line in lines
                if line.startswith("Policy Type:")
            ),
            "Unknown"
        )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": file_path.name,
                    "product_name": product_name,
                    "policy_type": policy_type,
                }
            )
        )

    if not documents:
        raise FileNotFoundError(
            f"No policy .txt files found in {POLICY_DIR}"
        )

    return documents


if __name__ == "__main__":
    documents = load_policy_documents()

    print(f"Loaded {len(documents)} policy documents.\n")

    for document in documents:
        print(document.metadata)