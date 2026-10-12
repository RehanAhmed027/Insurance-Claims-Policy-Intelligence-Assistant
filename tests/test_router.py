import unittest

from workflow.router import route_question


class TestRouter(unittest.TestCase):
    def test_claim_status_uses_sql(self):
        result = route_question({
            "question": "What is the status of CLM300500?"
        })

        self.assertEqual(result["route"], "sql")
        self.assertEqual(result["entity_type"], "claim")
        self.assertEqual(result["entity_id"], "CLM300500")

    def test_document_status_uses_sql(self):
        result = route_question({
            "question": "Which documents are missing for CLM300500?"
        })

        self.assertEqual(result["route"], "sql")

    def test_claim_analysis_uses_hybrid(self):
        result = route_question({
            "question": "Analyze claim CLM300500."
        })

        self.assertEqual(result["route"], "hybrid")

    def test_policy_wording_uses_rag(self):
        result = route_question({
            "question": (
                "What is the maternity waiting period "
                "under Health Secure Plus?"
            )
        })

        self.assertEqual(result["route"], "rag")

    def test_hospital_lookup_uses_sql(self):
        result = route_question({
            "question": "Is HOSP1000 in the network?"
        })

        self.assertEqual(result["route"], "sql")
        self.assertEqual(result["entity_type"], "hospital")

    def test_missing_claim_id_requests_clarification(self):
        result = route_question({
            "question": "What is my claim status?"
        })

        self.assertEqual(result["route"], "clarify")

    def test_multiple_ids_request_clarification(self):
        result = route_question({
            "question": "Compare CLM300500 and CLM300501."
        })

        self.assertEqual(result["route"], "clarify")

    def test_empty_question_requests_clarification(self):
        result = route_question({"question": ""})

        self.assertEqual(result["route"], "clarify")

    def test_customer_lookup_uses_sql(self):
        result = route_question({
            "question": "Show customer CUST147306."
        })

        self.assertEqual(result["route"], "sql")
        self.assertEqual(result["entity_type"], "customer")
        self.assertEqual(result["entity_id"], "CUST147306")

    def test_general_claim_procedure_uses_rag(self):
        result = route_question({
            "question": (
                "How do I submit a claim under Health Secure Plus?"
            )
        })

        self.assertEqual(result["route"], "rag")

    def test_required_document_rules_use_rag(self):
        result = route_question({
            "question": (
                "What documents are required for a claim "
                "under Family Care Gold?"
            )
        })

        self.assertEqual(result["route"], "rag")


if __name__ == "__main__":
    unittest.main()