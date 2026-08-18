import os
import tempfile
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.services.rag import ingest_document, chat_rag

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    chat_history: List[Dict] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Save uploaded file to a temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # Ingest into Qdrant with session_id
        ingest_document(tmp_path, session_id)
        
        return {"message": f"Successfully ingested {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = chat_rag(
            query_text=request.query,
            session_id=request.session_id,
            provider=request.provider,
            model_name=request.model_name,
            api_key=request.api_key,
            chat_history=request.chat_history
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
