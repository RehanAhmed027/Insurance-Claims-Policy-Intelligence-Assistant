from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from backend.schemas import (
    QuestionRequest,
    PolicyQuestionRequest,
)
from database.queries import get_claim_by_id
from guardrails.input_checks import validate_question
from rag.rag_chain import answer_policy_question
from workflow.graph import ask_assistant


app = FastAPI(
    title="Insurance GenAI Assistant",
    description="API for Insurance Claims and Policy Intelligence",
    version="1.0.0",
)


@app.exception_handler(RateLimitError)
async def handle_rate_limit(request, error):
    body = error.body if isinstance(error.body, dict) else {}
    details = body.get("error", body)

    if not isinstance(details, dict):
        details = {}

    quota_exhausted = (
        details.get("type") == "insufficient_quota"
        or details.get("code") in (
            "insufficient_quota",
            "credit_balance_exhausted",
        )
    )

    message = (
        "OpenAI API credits are unavailable. "
        "Check API billing. SQL-only questions still work."
        if quota_exhausted
        else "OpenAI rate limit reached. Please try again later."
    )

    return JSONResponse(
        status_code=503 if quota_exhausted else 429,
        content={"detail": message},
    )


@app.exception_handler(AuthenticationError)
async def handle_authentication(request, error):
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "OpenAI authentication failed. "
                "Check the API key configured in .env."
            )
        },
    )


@app.exception_handler(APIConnectionError)
async def handle_connection(request, error):
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Cannot connect to OpenAI. "
                "Check the server's internet connection "
                "and API configuration."
            )
        },
    )


@app.exception_handler(APIStatusError)
async def handle_api_status(request, error):
    return JSONResponse(
        status_code=502,
        content={
            "detail": (
                "OpenAI could not complete the request. "
                "Check the configured model and service availability."
            )
        },
    )


@app.get("/")
def home():
    return {
        "message": "Insurance GenAI API is running"
    }


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str):
    claim = get_claim_by_id(
        claim_id.strip().upper()
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return {"claim": claim}


@app.post("/policy/ask")
def ask_policy(request: PolicyQuestionRequest):
    # Validate the question before retrieval or an OpenAI call.
    try:
        question = validate_question(request.question)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    product_name = request.product_name.strip()

    if not product_name:
        raise HTTPException(
            status_code=400,
            detail="Please provide a policy product name.",
        )

    try:
        return answer_policy_question(
            question=question,
            product_name=product_name,
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Check the policy product name and server configuration."
            ),
        ) from None


@app.post("/ask")
def ask_question(request: QuestionRequest):
    result = ask_assistant(
        question=request.question,
        product_name=request.product_name,
    )

    return {
        "route": result["route"],
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "warnings": result.get("warnings", []),
    }