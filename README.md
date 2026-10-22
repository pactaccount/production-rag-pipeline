# Financial Document RAG Prototype

A FastAPI and React document question-answering prototype. It parses PDFs with LlamaParse, builds sentence-window nodes, stores embeddings in Qdrant, reranks retrieved nodes with Cohere, and sends context to a configurable LLM. The code explores an applied RAG architecture; the checked-in evaluation does **not** establish production accuracy.

## Current evidence

[`eval/smoke_report.json`](eval/smoke_report.json) is an early smoke run across six generated questions. It has no per-question details, and the Apple sample in `data/` is only a tiny fixture. One document reports 0 answer relevance. Those artifacts are insufficient for a retrieval-quality or hallucination-rate claim. The evaluation script now records generated, successfully evaluated, and failed question counts separately, and uses `null` when no scores were produced. Run `python eval/validate_report.py eval/smoke_report.json` to confirm that this historical report is incomplete.

For a credible benchmark, collect a fixed, human-reviewed set of questions with source passages and unanswerable examples; hold it out from prompt and retrieval tuning. Record per-question answers, retrieved sources, judge decisions, model versions, latency, and cost. Compare against a simple retrieval baseline on the same documents and queries.

## Architecture

1. `POST /api/ingest` parses a PDF, attaches a session identifier, and indexes sentence-window nodes in Qdrant.
2. `POST /api/chat` filters retrieval by session, reranks candidates, and generates an answer.
3. The React frontend calls the API. Optional user-supplied model keys are passed for that request.

The current code requires external LlamaCloud, Cohere, Gemini, and Qdrant services. Running the evaluation spends provider credits. Do not run it merely to verify installation.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` with `GEMINI_API_KEY`, `COHERE_API_KEY`, `LLAMA_CLOUD_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`. Never commit keys. Start the API with `uvicorn app.main:app --reload --port 8000` and the UI with `cd frontend && npm install && npm run dev`.

To run the paid evaluation intentionally:

```bash
python eval/dynamic_eval.py
python eval/validate_report.py eval/eval_results.json
```

The evaluation generates questions from the same documents used to build its temporary index, so it is a smoke test rather than held-out retrieval evidence. See [Documentation.md](Documentation.md) for implementation notes.
