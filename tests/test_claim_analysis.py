import unittest
from unittest.mock import patch

from workflow.nodes import rag_node


class TestClaimAnalysis(unittest.TestCase):
    @patch("workflow.nodes.analyze_claim")
    def test_hybrid_claim_uses_combined_analysis(self, mock_analyze):
        expected = {
            "answer": "Test analysis",
            "sources": [],
            "warnings": ["Test warning"],
        }
        mock_analyze.return_value = expected

        sql_results = {
            "claim": {
                "found": True,
                "claim": {"claim_id": "CLM300500"},
            }
        }

        result = rag_node({
            "question": "Analyze claim CLM300500.",
            "route": "hybrid",
            "entity_type": "claim",
            "sql_results": sql_results,
            "warnings": ["Test warning"],
        })

        mock_analyze.assert_called_once_with(
            question="Analyze claim CLM300500.",
            sql_results=sql_results,
            review_warnings=["Test warning"],
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()