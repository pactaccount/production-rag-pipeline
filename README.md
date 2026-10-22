# Financial Document RAG Prototype

A FastAPI and React document question-answering prototype. It parses PDFs with LlamaParse, builds sentence-window nodes, stores embeddings in Qdrant, reranks retrieved nodes with Cohere, and sends context to a configurable LLM. The code explores an applied RAG architecture. [Open the hosted demo](https://financial-rag-pipeline-te58.onrender.com/) or [read the measured evidence](docs/RESUME_EVIDENCE.md).

## Current evidence

The [fixed six-question hosted report](eval/results/hosted_2026-10-22.json) uses five selected pages from Apple's public 2025 10-K. Four questions returned correct source facts, while two requests returned HTTP 500 and no answer. That is **4/6 end-to-end completion with correct answers**, and **4/4 correctness among completed answers** on this small set. The unanswerable case did not complete, so abstention remains untested. The initial cold start took about 143 seconds; a subsequent one-page upload and answer also completed. These results are functional evidence, not a broad accuracy claim.

For a stronger benchmark, collect more human-reviewed questions across complete filings, including unanswerable cases. Record retrieved sources, manual support judgments, model versions, latency, and cost. Compare retrieval and reranking on the same held-out set. The current API returns answer text but no source excerpts, which limits user verification.

## Architecture

1. `POST /api/ingest` parses a PDF, attaches a session identifier, and indexes sentence-window nodes in Qdrant.
2. `POST /api/chat` filters retrieval by session, reranks candidates, and generates an answer.
3. The React frontend calls the API. Optional user-supplied model keys are passed for that request.

The current code requires external LlamaCloud, Cohere, Gemini, and Qdrant services. Running the hosted evaluation consumes provider quota; run it intentionally.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` with `GEMINI_API_KEY`, `COHERE_API_KEY`, `LLAMA_CLOUD_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`. Never commit keys. Start the API with `uvicorn app.main:app --reload --port 8000` and the UI with `cd frontend && npm install && npm run dev`.

To rerun the budgeted fixed evaluation intentionally, provide a local PDF copy of the [official Apple filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm):

```bash
python eval/hosted_fixed_eval.py --source /path/to/apple-2025-10k.pdf
```

The older `eval/dynamic_eval.py` generates questions from the indexed documents and is a smoke tool, not held-out evidence. See [Documentation.md](Documentation.md) for implementation notes.

## Résumé evidence

[Résumé evidence and verification](docs/RESUME_EVIDENCE.md) records the use case, engineering approach, test status, measured results, limits, and safe résumé wording.
