import unittest

from tools.customer_tool import customer_tool
from tools.interactions_tool import interactions_tool


class TestCustomerInteractions(unittest.TestCase):
    def test_existing_customer(self):
        result = customer_tool.invoke(
            {"customer_id": "CUST147306"}
        )

        self.assertTrue(result["found"])
        self.assertEqual(
            result["customer"]["customer_id"],
            "CUST147306",
        )

    def test_unknown_customer(self):
        result = customer_tool.invoke(
            {"customer_id": "CUST999999999"}
        )

        self.assertFalse(result["found"])

    def test_claim_interactions(self):
        result = interactions_tool.invoke(
            {"claim_id": "CLM300500"}
        )

        self.assertTrue(result["found"])
        self.assertEqual(
            result["returned_count"],
            len(result["interactions"]),
        )
        self.assertLessEqual(result["returned_count"], 10)

        for interaction in result["interactions"]:
            self.assertEqual(
                interaction["claim_id"],
                "CLM300500",
            )

    def test_unknown_claim(self):
        result = interactions_tool.invoke(
            {"claim_id": "CLM999999999"}
        )

        self.assertFalse(result["found"])


if __name__ == "__main__":
    unittest.main()