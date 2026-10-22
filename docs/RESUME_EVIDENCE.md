# Financial document RAG — résumé and demo evidence

## Problem and use case
Analysts need answers from long financial PDFs with support from source passages. This prototype explores ingestion, retrieval, reranking, and answer generation. A business use would require a human-checkable citation and an abstention path for unsupported questions. No analyst productivity outcome has been measured.

## Engineering approach
The FastAPI/React stack parses PDFs with LlamaParse, stores sentence-window embeddings in Qdrant, reranks with Cohere, and sends selected context to a configurable LLM. Evaluation scripts and a report validator exist, but the checked-in historical run is only a smoke artifact.

## Hard parts and limits
The [historical report](../eval/smoke_report.json) has six generated questions, zero successfully evaluated answers, and no per-question details. `python eval/validate_report.py eval/smoke_report.json` correctly labels it incomplete. It cannot support accuracy, hallucination-rate, or financial impact claims. The full pipeline requires external services and keys; do not include local `.env`, sample secrets, or private documents in a proof link.

## Verification and proof
The report validator was run on 2026-10-22 and returned the expected incomplete status. End-to-end answer quality was not verified in this audit. The recorded Render URL timed out after 50 seconds. Use [the demo-readiness branch](https://github.com/pactaccount/production-rag-pipeline/tree/demo-readiness-20261022) as an implementation link, and wait for a complete public sample-document demo before linking a deployment.

## Next measurement and résumé wording
Prepare 30–50 human-reviewed questions across public filings, with supporting passages and unanswerable cases. Compare simple retrieval against sentence-window reranking; report answer correctness, citation support, abstention, latency, and cost per question. Current safe wording: “Implemented a financial-PDF RAG prototype with parsing, sentence-window retrieval, Qdrant indexing, and reranking.” Use metric wording only after a complete saved report.
