# Financial document RAG — résumé and demo evidence

## Problem and use case
Analysts need to find facts in long financial filings without searching page by page. This prototype ingests a PDF and answers questions from retrieved passages. A real finance workflow needs citations that a reviewer can inspect, a reliable abstention path, access control, and monitoring. No analyst time savings or business impact have been measured.

## Engineering approach
The FastAPI/React stack parses PDFs with LlamaParse, builds sentence-window nodes, embeds and stores them in Qdrant, reranks with Cohere, and generates answers with a configured model. Sessions filter retrieval. The hosted evaluation extracts five pages from a public 2025 Apple 10-K, uploads them once, and asks six fixed questions. The [runner](../eval/hosted_fixed_eval.py), [case set](../eval/hosted_cases.json), [source filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm), and [per-question report](../eval/results/hosted_2026-10-22.json) document that path.

## Issues and limits
The free Render instance took about 143 seconds to wake; an earlier 50-second timeout did not establish failure. A separate one-page ingest and answer then succeeded in 11.0 and 2.3 seconds. In the fixed six-question run, four source facts were answered correctly, while two requests returned HTTP 500 without answers. The app now maps upstream quota errors to a clear HTTP 429 and hides raw provider error details. The exact cause of those two historical HTTP 500s was not captured. The current API returns answer text without source snippets, so a user cannot inspect citations in the UI. The unanswerable case did not finish, so abstention is unknown.

## Measured evidence
The six-question run shows **4/6 end-to-end completed and source-correct**, and **4/4 correct among completed answers**. This small selected-page check does not measure performance on a full filing or general answer quality. Two offline error-mapping tests pass. External LlamaCloud, Cohere, Gemini, and Qdrant services are required; each hosted run consumes provider quota. The local `data/apple_10k.pdf` is a tiny synthetic fixture and was *not* used as the source for this report.

## Résumé proof and next step
Use the [hosted demo](https://financial-rag-pipeline-te58.onrender.com/) beside this GitHub evidence page. Safe wording: “Built a hosted financial-PDF RAG workflow with sentence-window retrieval, Qdrant indexing, and reranking; validated source facts on a fixed public-filing smoke set.” For a headline accuracy number, expand to 30–50 human-reviewed questions across complete filings, add source citations and unanswerable cases, then measure answer support, abstention, completion rate, and p50/p95 latency. Do not claim production readiness or elimination of hallucinations.
