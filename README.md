# Contract Buddy

FastAPI + Streamlit app to extract, query, and audit contract PDFs using LangChain, Chroma, and Google Gemini.

## Features
- Upload PDF contracts and build a Chroma vector store.
- Extract structured contract data via FastAPI.
- RAG-based Q&A with citations.
- Contract risk audit.
- Streamlit UI for upload, extract, ask, and audit flows.

## Tech Stack
- FastAPI, Uvicorn
- Streamlit
- LangChain, Google Gemini, Chroma
- Python 3.11
- Docker / docker-compose

## Requirements
- Python 3.11
- Google API key (Gemini) in `.env`
- Docker + docker-compose (optional, recommended)

## Environment Variables
Create a `.env` file:
```
GOOGLE_API_KEY=your_key_here
```
Add any other secrets your provider requires. Do not commit this file.

## Local Development (without Docker)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Run API
uvicorn api:app --host 0.0.0.0 --port 8000

# In another shell, run Streamlit UI
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```
API at `http://localhost:8000`, UI at `http://localhost:8501`.

## Docker
Build and run both services:
```bash
docker compose up --build
```
- API: `http://localhost:8000`
- Streamlit UI: `http://localhost:8501`

Persistent volumes (host-mounted):
- `docs/` for uploads
- `chroma_langchain_db/` for vector store

## Key Endpoints (FastAPI)
- `GET /health` – service health
- `POST /ingest` – upload PDF (multipart/form-data, key: `file`)
- `GET /extract` – structured extraction (optional `filename` query)
- `GET /rag` – retrieve context for a query (`query` param)
- `POST /ask` – final LLM answer with RAG context
- `POST /ask/stream` – streaming tokens
- `GET /audit` – contract risk audit (optional `filename`)

### Example cURL calls
```bash
# Health
curl http://localhost:8000/health

# Upload (replace sample.pdf with your file)
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample.pdf;type=application/pdf"

# Extract (latest file or specify ?filename=sample.pdf)
curl "http://localhost:8000/extract"
curl "http://localhost:8000/extract?filename=sample.pdf"

# RAG retrieval
curl "http://localhost:8000/rag?query=What is the contract about?"

# Ask (final answer using previous RAG context)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the contract", "rag_data": {"output": "text from rag", "citations": []}}'

# Audit (latest file or specify filename)
curl "http://localhost:8000/audit"
curl "http://localhost:8000/audit?filename=sample.pdf"
```

## Using the UI
1) Set API URL in the sidebar (defaults to `http://localhost:8000`).
2) Upload a PDF, then run Extract, Ask, or Audit from the tabs.

## Project Structure
- `api.py` – FastAPI routes
- `main.py` – LLM and RAG orchestration
- `rag.py` – embeddings, Chroma vector store
- `app.py` – Streamlit frontend
- `docs/` – uploaded PDFs and metadata (git-ignored)
- `chroma_langchain_db/` – persisted vector store (git-ignored)

## Notes
- `.env`, `.venv`, uploads, and vector DB are git-ignored.
- If you need native deps for some wheels, the Docker image installs `build-essential`.
