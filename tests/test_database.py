import unittest

from database.queries import (
    get_claim_by_id,
    get_claim_documents,
    get_policy_by_id,
    get_hospital_by_id,
)


class TestDatabase(unittest.TestCase):
    def test_existing_claim(self):
        claim = get_claim_by_id("CLM300500")

        self.assertIsNotNone(claim)
        self.assertEqual(claim["claim_id"], "CLM300500")
        self.assertEqual(claim["claim_status"], "Under Review")
        self.assertEqual(claim["claim_amount"], 44184)

    def test_unknown_claim(self):
        claim = get_claim_by_id("CLM999999999")

        self.assertIsNone(claim)

    def test_sql_injection_is_not_executed(self):
        claim = get_claim_by_id(
            "CLM300500' OR 1=1 --"
        )

        self.assertIsNone(claim)

    def test_claim_documents(self):
        documents = get_claim_documents("CLM300500")

        self.assertEqual(len(documents), 5)

        for document in documents:
            self.assertEqual(
                document["claim_id"],
                "CLM300500",
            )
            self.assertEqual(
                document["verification_status"],
                "Verified",
            )

    def test_linked_policy(self):
        claim = get_claim_by_id("CLM300500")
        self.assertIsNotNone(claim)

        policy = get_policy_by_id(claim["policy_id"])
        self.assertIsNotNone(policy)

        self.assertEqual(
            policy["policy_id"],
            claim["policy_id"],
        )

    def test_existing_hospital(self):
        hospital = get_hospital_by_id("HOSP1000")

        self.assertIsNotNone(hospital)
        self.assertEqual(hospital["hospital_id"], "HOSP1000")


if __name__ == "__main__":
    unittest.main()