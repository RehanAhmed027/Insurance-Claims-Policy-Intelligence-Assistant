# Enterprise Insurance Claims & Policy Intelligence Assistant

A local insurance assistant that answers structured-data questions
using SQLite and policy questions using retrieval-augmented generation.

This individual practice project uses synthetic insurance data.

## Technology Stack

- Python
- SQLite and SQLAlchemy
- FastAPI
- Streamlit
- LangChain and LangGraph
- ChromaDB
- Hugging Face embeddings
- BM25 keyword search
- Cross-encoder reranking
- OpenAI for answer generation
- Model Context Protocol (MCP)

## Architecture

Streamlit → FastAPI → LangGraph router → SQL tools and/or policy RAG
→ answer with sources and review warnings.

Processing paths:

- SQL: router → SQL tools → formatted record answer
- RAG: router → hybrid retrieval → reranking → LLM → answer
- Hybrid claim: router → SQL tools → retrieval → reranking
  → combined claim-analysis chain → final answer
- Clarification: router → request for missing information

SQL-only questions do not call an LLM.

The router uses deterministic rules. The LLM does not autonomously
choose SQL tools or generate SQL statements.

A separate MCP server exposes the existing SQL tools to MCP clients.
The current LangGraph workflow calls those tools directly.

## Project Structure

```text
Insurance _Claims _&_Policy_Intelligence_Assistant/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── schemas.py
├── data/
│   ├── csv_files/
│   └── policy_documents/
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── load_data.py
│   └── queries.py
├── evaluation/
│   ├── __init__.py
│   └── evaluate.py
├── frontend/
│   └── streamlit_app.py
├── guardrails/
│   ├── __init__.py
│   ├── input_checks.py
│   └── answer_checks.py
├── mcp_service/
│   ├── __init__.py
│   ├── server.py
│   └── client_demo.py
├── prompts/
│   ├── __init__.py
│   └── templates.py
├── rag/
│   ├── __init__.py
│   ├── document_loader.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── hybrid_search.py
│   ├── reranker.py
│   ├── rag_chain.py
│   └── claim_analysis.py
├── tests/
│   ├── test_database.py
│   ├── test_retrieval.py
│   ├── test_router.py
│   ├── test_customer_interactions.py
│   └── test_claim_analysis.py
├── tools/
│   ├── __init__.py
│   ├── claims_tool.py
│   ├── documents_tool.py
│   ├── policy_tool.py
│   ├── hospital_tool.py
│   ├── customer_tool.py
│   └── interactions_tool.py
├── workflow/
│   ├── __init__.py
│   ├── state.py
│   ├── router.py
│   ├── nodes.py
│   └── graph.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Local setup also creates:

- `.env`: private configuration
- `.venv-1/`: Python virtual environment
- `database/insurance.db`: generated SQLite database
- `chroma_db/`: persistent policy vector storage

Exclude these local files and folders from Git.

## Dataset

Place the business CSV files in `data/csv_files/`:

| File | Records | Purpose |
| --- | ---: | --- |
| customers.csv | 50,000 | Customer profiles and KYC status |
| policies.csv | 75,000 | Policy schedules and products |
| claims.csv | 120,000 | Claim details, status and amounts |
| claim_documents.csv | 600,010 | Upload and verification statuses |
| hospitals.csv | 1,200 | Hospital details and network status |
| customer_interactions.csv | 180,000 | Recorded support interactions |

Also keep these reference files in `data/csv_files/`:

- `evaluation_questions.csv`
- `README_DATASET.txt`

Reference files are not loaded as business tables.

Place the ten policy text files in `data/policy_documents/`.

Policy documents are split into 150 numbered sections. Each chunk
retains its product name, policy type, filename, section heading
and stable chunk ID.

## Setup

Run commands from the main project folder.

Create a virtual environment if one does not already exist:

```powershell
python -m venv .venv-1
```

Activate it and install dependencies:

```powershell
.\.venv-1\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Ensure `requirements.txt` includes:

```text
langchain-openai
mcp>=1.12,<2
```

The MCP implementation uses the version 1 SDK API.

### Current LLM Configuration: OpenAI

Create `.env` in the main project folder:

```dotenv
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Replace the API key placeholder with your actual key.
Keep the entire key on one line.

The answer chains load this file using:

```python
load_dotenv(BASE_DIR / ".env", override=True)
```

Keep `.env.example` as a shareable template:

```dotenv
OPENAI_API_KEY=replace_with_your_api_key
OPENAI_MODEL=gpt-4.1-mini
```

Never commit `.env` or share your actual key.

OpenAI-generated answers require available API credits.
SQL queries, local retrieval, reranking, MCP and retrieval evaluation
do not require OpenAI credits.

A switch to Ollama is planned but has not yet been implemented.

## Prepare the Data

Load the six business CSV files into SQLite:

```powershell
python -m database.load_data
```

Rerunning this command replaces the six business tables with CSV data.

Build the policy vector store:

```powershell
python -m rag.vector_store
```

This stores policy chunks and embeddings in ChromaDB.

Embedding and reranking models require internet access on their first
download. Subsequent runs can use cached models.

Stable chunk IDs prevent duplicate entries when the same sections
are ingested again. Removed files or changed section IDs can leave
obsolete entries. Recreate the policy collection when needed.

## Start the Application

The current application uses FastAPI on port 8001.

Start FastAPI in one activated terminal:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

Wait for `Application startup complete` and keep the terminal running.

Ensure `frontend/streamlit_app.py` contains:

```python
API_URL = "http://127.0.0.1:8001"
```

Start Streamlit in a second activated terminal:

```powershell
.\.venv-1\Scripts\Activate.ps1
python -m streamlit run frontend/streamlit_app.py
```

Open:

- API documentation: http://127.0.0.1:8001/docs
- Streamlit interface: http://localhost:8501

Keep both terminals running while using the application.
Restart FastAPI after backend changes when running without auto-reload.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Check that the API is running |
| GET | `/claims/{claim_id}` | Retrieve one claim |
| POST | `/policy/ask` | Ask about a specified policy product |
| POST | `/ask` | Process a question through LangGraph |

Example SQL request for `/ask`:

```json
{
  "question": "What is the status of CLM300500?",
  "product_name": ""
}
```

Example policy request:

```json
{
  "question": "What is the maternity waiting period?",
  "product_name": "Health Secure Plus"
}
```

Example hybrid request for `/ask`:

```json
{
  "question": "Analyze claim CLM300500.",
  "product_name": ""
}
```

## Example Questions

- What is the status of CLM300500?
- Which documents are missing for CLM300500?
- Is HOSP1000 in the network?
- Show customer CUST147306.
- What is the maternity waiting period under Health Secure Plus?
- Analyze claim CLM300500.

The router supports one exact claim, policy, hospital or customer ID
per question. It does not support multi-record comparisons or general
SQL analytics.

## Retrieval Design

Policy retrieval follows these steps:

1. Filter candidates to the selected product.
2. Retrieve similar sections from ChromaDB.
3. Retrieve keyword matches using BM25.
4. Merge rankings using Reciprocal Rank Fusion.
5. Rerank candidates with a cross-encoder.
6. Supply selected sections to the answer-generation prompt.

Models:

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Reranking: `cross-encoder/ms-marco-MiniLM-L6-v2`

Structured SQL records are not embedded into the policy vector store.

## SQL Tools

Registered LangChain tools retrieve:

- Claim details
- Document statuses
- Policy records
- Hospital details
- Customer profiles
- Up to ten recent interactions for a claim

The SQL node flags claim-policy customer-ID, policy-type and date
inconsistencies for review.

Direct customer-ID questions use SQL. Customer and interaction
context is also displayed in hybrid claim answers.

## Combined Claim Analysis

`rag/claim_analysis.py` prepares selected SQL facts and retrieves
policy evidence for the claim's recorded product.

The combined analysis prompt receives:

- The user's question
- Claim and policy facts
- Recorded document statuses
- Hospital details when available
- Recent interaction details
- Retrieved policy sections
- Review warnings

Customer profiles and names are excluded from the model payload.
Selected claim facts can still contain sensitive information in a
real dataset; the supplied dataset is synthetic.

The model is instructed to separate facts, policy conditions and
uncertainty, cite evidence, and avoid guaranteeing approval.

The final response also displays deterministic SQL facts and warnings
for comparison with the generated analysis.

Generated claim analysis remains unverified.
This feature does not constitute a complete eligibility assessment.

## MCP Interface

The local MCP server exposes six tools:

| MCP tool | Purpose |
| --- | --- |
| lookup_claim | Retrieve a claim record |
| lookup_documents | Retrieve claim-document statuses |
| lookup_policy | Retrieve a policy record |
| lookup_hospital | Retrieve hospital details |
| lookup_customer | Retrieve a customer profile |
| lookup_interactions | Retrieve recent claim interactions |

Run the client demonstration:

```powershell
python -m mcp_service.client_demo
```

The client:

1. Launches `mcp_service.server` as a subprocess.
2. Connects using the stdio transport.
3. Initializes an MCP session.
4. Discovers the six tools.
5. Calls `lookup_claim` for `CLM300500`.
6. Displays the result and closes the session.

MCP discovery and claim lookup have been verified.
The claim lookup returned `isError: false`.

The current result is returned as JSON text inside MCP content.
A null `structuredContent` field does not indicate tool failure.

The current LangGraph workflow calls the underlying tools directly.
It does not use the MCP client.

No LLM, API credits or FastAPI server are required for the MCP demo.
Do not add ordinary stdout print statements to the stdio server,
because stdout carries MCP protocol messages.

## Tests

Run all automated tests:

```powershell
python -m unittest discover -s tests -v
```

The current suite contains 26 tests:

| Test file | Tests |
| --- | ---: |
| test_database.py | 6 |
| test_retrieval.py | 6 |
| test_router.py | 9 |
| test_customer_interactions.py | 4 |
| test_claim_analysis.py | 1 |

Tests cover SQL queries, routing, product filtering, chunk IDs,
reranking and customer/interaction tools.

The claim-analysis test mocks the analysis function. It confirms
workflow dispatch, not generated-answer quality.

The MCP client demonstration is a separate integration check.

## Retrieval Evaluation

Run:

```powershell
python -m evaluation.evaluate
```

The supplied evaluation CSV uses these headers:

| Header | Meaning |
| --- | --- |
| 0 | Evaluation ID |
| 1 | Product name |
| 2 | Question |
| 3 | Expected answer |
| 4 | Expected section |

Evaluation measures whether the expected section appears in the top
three reranked results.

Literal-answer matching is a diagnostic. Equivalent wording can
produce a failed literal match.

### Observed Results

- Questions evaluated: 5
- Expected-section hit rate@3: 100%
- Literal-answer matching failed on three questions.
- Results cover the supplied seed questions only.
- These results do not measure generated-answer correctness.

Expand evaluation to 50–100 manually verified questions, including
routing, insufficient evidence, data conflicts and citation support.

## Guardrails and Limitations

- SQL values are passed as bound parameters.
- Basic input checks flag selected override and modification requests.
- Both `/ask` and `/policy/ask` validate user questions.
- Input checks do not provide complete prompt-injection protection.
- Citation checks flag missing or unknown evidence IDs.
- Citation checks do not prove that cited text supports each statement.
- Combined analysis allows citations to supplied SQL labels and
  retrieved policy section IDs.
- Document statuses do not certify required-document completeness.
- Fraud scores and manual-review flags do not establish fraud.
- Support resolution status does not establish the claim outcome.
- Active policy status does not resolve coverage-date inconsistencies.
- Automated answers do not guarantee coverage or claim approval.
- The router uses basic rules and needs broader evaluation.
- SQL answers currently display more context than some questions require.
- The application has no customer authentication or authorization.
- MCP tools expose synthetic records to the local client without
  customer-level authorization.

Keep the training application local.
The synthetic data may contain inconsistent or incomplete records.

## API Error Handling

The API returns clear messages for OpenAI credit exhaustion,
rate limits, authentication failures and connection errors.

Streamlit displays these messages directly.

When API credits are unavailable, the API returns a 503 response
explaining the billing issue. SQL-only questions remain available.

A blocked `/policy/ask` override request has been verified to return
400 before retrieval or an LLM call.

## Current Status

Implemented and exercised:

- CSV ingestion into SQLite
- SQL tools and direct customer lookup
- Policy loading and section chunking
- ChromaDB storage
- Hybrid retrieval and reranking
- LangGraph SQL workflow
- FastAPI and Streamlit integration
- Basic input and citation checks
- Retrieval evaluation
- OpenAI credit-exhaustion error handling
- Input validation on both question endpoints
- Combined-analysis SQL context preparation
- Mocked dispatch to the combined claim-analysis function
- MCP tool discovery and claim lookup

Still pending:

- Ollama integration if replacing OpenAI
- Successful generated policy-answer testing
- Successful generated claim-analysis testing
- Generated-answer grounding and citation-support evaluation
- Expanded evaluation with 50–100 cases
- Better routing for general claim-procedure questions
- More focused SQL answers

This project is for learning and demonstration, not real claim decisions.