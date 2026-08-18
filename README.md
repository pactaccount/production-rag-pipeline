# Production Multi-Modal RAG Pipeline

![Hero Image](frontend/src/assets/hero.png)

A high-performance, production-ready Retrieval-Augmented Generation (RAG) system engineered for complex financial and technical documents. Built with a modern, decoupled stack, this project transforms standard text-based RAG into a fully multimodal, highly precise intelligence engine.

## High-Level Overview & Features

This project abandons basic, naive vector similarity in favor of a robust, enterprise-grade architecture:

* **Multimodal Extraction**: Instead of stripping charts and tables from PDFs, this pipeline uses **LlamaParse** to parse tables semantically and extract charts as visual nodes. You can ask the LLM to analyze the actual trends in a graph from a 10-K filing!
* **Sentence Window Chunking**: To solve the "chunk size dilemma", the system breaks documents down sentence-by-sentence. It embeds only the precise sentence for retrieval, but dynamically injects a window of surrounding context (e.g., the 3 sentences before and after) into the LLM prompt. This ensures ultra-precise vector matching *without* losing context.
* **Two-Stage Re-ranking**: We use Qdrant for initial retrieval (Stage 1), followed by a **Cohere Cross-Encoder** (Stage 2) to mathematically rescore the top candidates against the exact user query. This filters out irrelevant keyword matches and virtually eliminates hallucination.
* **BYOK Architecture (Bring Your Own Key)**: The system defaults to Gemini 1.5 Pro, but natively supports dynamic model routing. Recruiters and users can securely plug in their own API keys to test the system with OpenAI (GPT-4o), Anthropic (Claude 3.5), or Groq models without depleting the server's credits!
* **Automated Evaluation**: Fully integrated with the **Ragas** framework to mathematically prove the system's accuracy (Faithfulness and Answer Relevancy).

## Tentative Architecture

1. **Document Ingestion Layer**: 
   * PDFs (e.g., SEC Form 10-Ks) are parsed by `LlamaParse`.
   * Tables are converted to markdown; images/charts are isolated.
2. **Indexing & Storage Layer**:
   * Data is chunked using `SentenceWindowNodeParser`.
   * Embedded via `Cohere (embed-english-v3.0)`.
   * Stored in a dual-index architecture in `Qdrant Cloud`.
3. **Retrieval & Reranking Layer**:
   * Top-k vector retrieval via Qdrant.
   * Reranking via `CohereRerank` cross-encoder.
4. **Synthesis Layer**:
   * The final context (text + images) is injected into `Gemini 1.5 Pro` (Multimodal).
   * Generates a hallucination-free, highly contextual response.
5. **Presentation Layer**:
   * API served via `FastAPI`.
   * UI built with `React`, `Vite`, `TailwindCSS`, and `React Three Fiber` for dynamic 3D visuals.

## Getting Started

### Prerequisites
* Python 3.12+
* Node.js 18+
* API Keys for: Gemini, Cohere, LlamaCloud, and Qdrant.

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/pactaccount/production-rag-pipeline.git
cd production-rag-pipeline
```

2. **Set up the Backend Environment:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Configure Environment Variables:**
Create a `.env` file in the root directory and add your API keys:
```env
GEMINI_API_KEY=your_gemini_key
COHERE_API_KEY=your_cohere_key
LLAMA_CLOUD_API_KEY=your_llama_cloud_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
```

4. **Run the FastAPI Server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Run the React Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## In-Depth Research Documentation
For a deep dive into the algorithmic design, technical implementation details, and the rigorous quantitative evaluation results (proving a 1.0 score in Faithfulness), please refer to the official [Documentation](Documentation.md) included in this repository.
