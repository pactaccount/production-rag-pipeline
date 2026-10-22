"""Budgeted hosted RAG check: six fixed questions, one five-page public filing extract.

This uses the project's configured LlamaParse, Cohere, Gemini and Qdrant services.
It is intentionally manual to run because it consumes provider usage.
"""

import argparse
import hashlib
import json
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from pypdf import PdfReader, PdfWriter


PAGES = [0, 4, 21, 41, 50]  # Zero-based PDF pages; chosen before questions run.
SOURCE_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"


def run(source, base_url, output):
    source = Path(source)
    reader = PdfReader(str(source))
    writer = PdfWriter()
    for index in PAGES:
        writer.add_page(reader.pages[index])
    cases = json.loads((Path(__file__).parent / "hosted_cases.json").read_text())
    session_id = "resume-eval-" + uuid.uuid4().hex[:12]
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temporary:
        writer.write(temporary)
        extracted_path = Path(temporary.name)
    try:
        start = time.monotonic()
        with extracted_path.open("rb") as file:
            response = requests.post(
                base_url.rstrip("/") + "/api/ingest",
                files={"file": ("apple-2025-selected-pages.pdf", file, "application/pdf")},
                data={"session_id": session_id}, timeout=180,
            )
        ingest_seconds = round(time.monotonic() - start, 2)
        response.raise_for_status()
        rows = []
        for case in cases:
            start = time.monotonic()
            try:
                response = requests.post(
                    base_url.rstrip("/") + "/api/chat",
                    json={"query": case["question"], "session_id": session_id, "chat_history": []},
                    timeout=150,
                )
                answer = response.json().get("response", "")
                row = {**case, "answer": answer, "http_status": response.status_code,
                       "latency_seconds": round(time.monotonic() - start, 2),
                       "error_category": None if response.ok else f"backend_http_{response.status_code}",
                       "human_correct": None, "review_note": "Pending source-grounded review"}
            except Exception as exc:
                row = {**case, "answer": "", "http_status": None,
                       "latency_seconds": round(time.monotonic() - start, 2),
                       "error_category": type(exc).__name__,
                       "human_correct": None, "review_note": "Request did not complete"}
            rows.append(row)
            print(case["id"], row["http_status"], repr(row["answer"][:180]), flush=True)
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "base_url": base_url, "source_url": SOURCE_URL,
            "source_pdf_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "pdf_pages_included_zero_based": PAGES,
            "ingest_seconds": ingest_seconds,
            "protocol": "Six fixed questions, five selected pages, exact source-fact human review; one unanswerable case",
            "cases": rows,
        }
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
        print("Saved", output)
    finally:
        extracted_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Local PDF copy of the public 2025 Apple 10-K")
    parser.add_argument("--base-url", default="https://financial-rag-pipeline-te58.onrender.com")
    parser.add_argument("--output", default="eval/results/hosted_2026-10-22.json")
    args = parser.parse_args()
    run(args.source, args.base_url, args.output)
