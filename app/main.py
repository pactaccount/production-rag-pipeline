from fastapi import FastAPI
from app.api.routes import router
import phoenix as px
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SEC 10-K RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local Phoenix tracing is disabled in production to prevent timeout crashes
# and because cloud providers only expose a single port.

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app.include_router(router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Production RAG Pipeline Backend is running."}

# Serve Frontend statically if it exists (for Hugging Face Spaces / Docker)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve index.html for all non-API paths for React Router compatibility
        return FileResponse(os.path.join(frontend_dist, "index.html"))
