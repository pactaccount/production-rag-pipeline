import os
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.cohere import CohereEmbedding
from llama_parse import LlamaParse
from llama_index.core import Settings
from qdrant_client import QdrantClient

from app.core.config import settings

# Configure Settings globally
os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
os.environ["LLAMA_CLOUD_API_KEY"] = settings.LLAMA_CLOUD_API_KEY

Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = CohereEmbedding(
    model_name="embed-english-v3.0", 
    cohere_api_key=settings.COHERE_API_KEY
)
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Initialize Qdrant Client
qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
text_collection = "sec_10k_text"
image_collection = "sec_10k_images"

def get_storage_context():
    text_store = QdrantVectorStore(client=qdrant_client, collection_name=text_collection)
    image_store = QdrantVectorStore(client=qdrant_client, collection_name=image_collection)
    return StorageContext.from_defaults(vector_store=text_store, image_store=image_store)

def get_index():
    storage_context = get_storage_context()
    try:
        # Check if index is already populated
        from llama_index.core.indices import MultiModalVectorStoreIndex
        index = MultiModalVectorStoreIndex.from_vector_store(
            vector_store=storage_context.vector_store,
            image_vector_store=storage_context.image_store
        )
        return index
    except Exception as e:
        print(f"Index not found: {e}")
        return None

from typing import List, Dict, Optional
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter

from llama_index.multi_modal_llms.gemini import GeminiMultiModal

def get_dynamic_llm(provider: Optional[str], model_name: Optional[str], api_key: Optional[str]):
    # Fallback to server key if user didn't provide one
    if not api_key:
        return GeminiMultiModal(model="models/gemini-1.5-pro-latest", api_key=settings.GEMINI_API_KEY)
        
    return GeminiMultiModal(model=model_name or "models/gemini-1.5-pro-latest", api_key=api_key)

from llama_index.core.node_parser import SentenceWindowNodeParser

from llama_index.core.schema import ImageDocument
from llama_index.core.indices import MultiModalVectorStoreIndex

def ingest_document(file_path: str, session_id: str):
    print("Parsing document using LlamaParse...")
    parser = LlamaParse(result_type="markdown")
    documents = parser.load_data(file_path)
    
    print("Extracting images from document...")
    images_dir = os.path.join(os.path.dirname(file_path), f"images_{session_id}")
    os.makedirs(images_dir, exist_ok=True)
    images = parser.get_images(documents, download_path=images_dir)
    
    image_docs = []
    for img in images:
        img_doc = ImageDocument(image_path=img["path"])
        img_doc.metadata["session_id"] = session_id
        image_docs.append(img_doc)
    
    # Attach session_id to metadata
    for doc in documents:
        doc.metadata["session_id"] = session_id
        
    print("Parsing nodes with Sentence Window Chunking...")
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    nodes = node_parser.get_nodes_from_documents(documents)
    
    storage_context = get_storage_context()
    
    print(f"Embedding {len(nodes)} text nodes and {len(image_docs)} images...")
    index = MultiModalVectorStoreIndex(
        nodes=nodes,
        image_documents=image_docs,
        storage_context=storage_context,
        show_progress=True
    )
            
    return index

from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.postprocessor import MetadataReplacementPostProcessor

def chat_rag(query_text: str, session_id: str, provider: Optional[str], model_name: Optional[str], api_key: Optional[str], chat_history: List[Dict]):
    index = get_index()
    if index is None:
        return "No documents have been ingested yet. Please ingest a PDF first."
    
    llm = get_dynamic_llm(provider, model_name, api_key)
    
    history_msgs = []
    for msg in chat_history:
        role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
        history_msgs.append(ChatMessage(role=role, content=msg["content"]))
        
    filters = MetadataFilters(
        filters=[ExactMatchFilter(key="session_id", value=session_id)]
    )
    
    cohere_rerank = CohereRerank(api_key=settings.COHERE_API_KEY, top_n=3)
    metadata_replacement = MetadataReplacementPostProcessor(target_metadata_key="window")
    
    chat_engine = index.as_chat_engine(
        llm=llm,
        chat_mode="condense_plus_context",
        filters=filters,
        node_postprocessors=[metadata_replacement, cohere_rerank],
        similarity_top_k=10 # Fetch 10, then rerank down to 3
    )
    
    response = chat_engine.chat(query_text, chat_history=history_msgs)
    return str(response)
