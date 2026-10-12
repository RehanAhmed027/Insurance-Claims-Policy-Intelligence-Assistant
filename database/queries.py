from sqlalchemy import text

from database.connection import engine


def get_claim_by_id(claim_id: str):
    query = text("""
        SELECT *
        FROM claims
        WHERE claim_id = :claim_id
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"claim_id": claim_id}
        ).mappings().first()

    return dict(row) if row is not None else None

def get_claim_documents(claim_id: str):
    query = text("""
        SELECT *
        FROM claim_documents
        WHERE claim_id = :claim_id
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"claim_id": claim_id}
        ).mappings().all()

    return [dict(row) for row in rows]

def get_policy_by_id(policy_id: str):
    query = text("""
        SELECT *
        FROM policies
        WHERE policy_id = :policy_id
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"policy_id": policy_id}
        ).mappings().first()

    return dict(row) if row is not None else None

def get_hospital_by_id(hospital_id: str):
    query = text("""
        SELECT *
        FROM hospitals
        WHERE hospital_id = :hospital_id
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"hospital_id": hospital_id}
        ).mappings().first()

    return dict(row) if row is not None else None

def get_claim_interactions(claim_id: str):
    query = text("""
        SELECT
            interaction_id,
            claim_id,
            interaction_date,
            channel,
            intent,
            sentiment,
            resolution_status
        FROM customer_interactions
        WHERE claim_id = :claim_id
        ORDER BY interaction_date DESC, interaction_id DESC
        LIMIT 10
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"claim_id": claim_id}
        ).mappings().all()

    return [dict(row) for row in rows]

def get_customer_by_id(customer_id: str):
    query = text("""
        SELECT *
        FROM customers
        WHERE customer_id = :customer_id
    """)

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"customer_id": customer_id}
        ).mappings().first()

    return dict(row) if row is not None else None

if __name__ == "__main__":
    claim = get_claim_by_id("CLM300500")

    if claim is None:
        print("Claim not found.")
    else:
        for column, value in claim.items():
            print(f"{column}: {value}")