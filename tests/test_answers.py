import unittest

from workflow.nodes import final_answer_node


class TestAnswers(unittest.TestCase):
    def test_claim_status_is_focused(self):
        result = final_answer_node({
            "question": "What is the status of CLM300500?",
            "route": "sql",
            "entity_type": "claim",
            "sql_results": {
                "claim": {
                    "found": True,
                    "claim": {
                        "claim_id": "CLM300500",
                        "claim_status": "Under Review",
                    },
                },
            },
            "warnings": ["Verify policy dates."],
            "sources": [],
        })

        self.assertEqual(
            result["answer"],
            "Claim CLM300500 status: Under Review. [SQL:claims]",
        )
        self.assertEqual(
            result["warnings"],
            ["Verify policy dates."],
        )

    def test_unknown_claim_status(self):
        result = final_answer_node({
            "question": "What is the status of CLM999999999?",
            "route": "sql",
            "entity_type": "claim",
            "sql_results": {
                "claim": {
                    "found": False,
                    "message": "Claim not found.",
                },
            },
            "warnings": [],
            "sources": [],
        })

        self.assertEqual(
            result["answer"],
            "Claim not found.",
        )


if __name__ == "__main__":
    unittest.main()