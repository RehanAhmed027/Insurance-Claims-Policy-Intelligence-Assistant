import csv

from config import CSV_DIR
from rag.hybrid_search import hybrid_search
from rag.reranker import rerank_documents


def evaluate_retrieval():
    file_path = CSV_DIR / "evaluation_questions.csv"

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Evaluation file not found: {file_path}"
        )

    results = []

    with file_path.open(
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        # This dataset uses numbered headers:
        # 0 = ID, 1 = product, 2 = question,
        # 3 = expected answer, 4 = expected section
        required_columns = {"0", "1", "2", "3", "4"}

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                "Expected evaluation CSV headers: 0,1,2,3,4"
            )

        for row in reader:
            question = row["2"].strip()
            product_name = row["1"].strip()
            expected_answer = row["3"].strip()
            expected_section = row["4"].strip()

            candidates = hybrid_search(
                question=question,
                product_name=product_name,
                k=10,
            )

            documents = rerank_documents(
                question=question,
                documents=candidates,
                top_k=3,
            )

            section_hit = any(
                expected_section.casefold()
                in document.metadata["section"].casefold()
                for document in documents
            )

            context = "\n".join(
                document.page_content
                for document in documents
            )

            literal_answer_hit = (
                expected_answer.casefold() in context.casefold()
            )

            results.append({
                "id": row["0"],
                "question": question,
                "section_hit": section_hit,
                "literal_answer_hit": literal_answer_hit,
            })

            print(f"\n{row['0']}: {question}")
            print(f"Product: {product_name}")
            print(f"Expected section in top 3: {section_hit}")
            print(f"Literal expected answer found: {literal_answer_hit}")
            print(
                "Retrieved sections:",
                [doc.metadata["section"] for doc in documents],
            )

    if not results:
        raise ValueError("The evaluation CSV contains no questions.")

    section_hits = sum(
        result["section_hit"] for result in results
    )

    print("\nEvaluation summary")
    print(f"Questions evaluated: {len(results)}")
    print(
        f"Expected-section hit rate@3: "
        f"{section_hits / len(results):.1%}"
    )

    return results


if __name__ == "__main__":
    evaluate_retrieval()