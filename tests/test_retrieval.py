import unittest

from rag.document_loader import load_policy_documents
from rag.chunking import chunk_policy_documents
from rag.hybrid_search import hybrid_search
from rag.reranker import rerank_documents


class TestRetrieval(unittest.TestCase):
    def test_document_count(self):
        documents = load_policy_documents()

        self.assertEqual(len(documents), 10)

    def test_chunk_ids_are_unique(self):
        chunks = chunk_policy_documents(
            load_policy_documents()
        )

        chunk_ids = [
            chunk.metadata["chunk_id"]
            for chunk in chunks
        ]

        self.assertEqual(len(chunks), 150)
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))

    def test_product_filter(self):
        results = hybrid_search(
            question="What is the maternity waiting period?",
            product_name="Health Secure Plus",
            k=6,
        )

        self.assertTrue(results)

        for document in results:
            self.assertEqual(
                document.metadata["product_name"],
                "Health Secure Plus",
            )

    def test_maternity_section_is_retrieved(self):
        results = hybrid_search(
            question="What is the maternity waiting period?",
            product_name="Health Secure Plus",
            k=6,
        )

        self.assertTrue(
            any(
                document.metadata["section_number"] == 5
                for document in results
            )
        )

    def test_reranker_returns_candidate_documents(self):
        question = "What is the maternity waiting period?"

        candidates = hybrid_search(
            question=question,
            product_name="Health Secure Plus",
            k=10,
        )

        results = rerank_documents(
            question=question,
            documents=candidates,
            top_k=3,
        )

        candidate_ids = {
            document.metadata["chunk_id"]
            for document in candidates
        }

        self.assertEqual(len(results), 3)

        scores = []

        for document in results:
            self.assertIn(
                document.metadata["chunk_id"],
                candidate_ids,
            )
            scores.append(document.metadata["rerank_score"])

        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_unknown_product(self):
        with self.assertRaises(ValueError):
            hybrid_search(
                question="What is covered?",
                product_name="Unknown Product",
            )


if __name__ == "__main__":
    unittest.main()