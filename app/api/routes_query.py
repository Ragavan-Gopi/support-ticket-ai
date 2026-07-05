import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.config import DB_PATH, CHROMA_DIR, CHROMA_COLLECTION_NAME
from app.core.rag import (
    retrieve_relevant_tickets,
    answer_question_with_rag,
    index_tickets
)
from app.core.schemas import (
    QueryRetrieveRequest,
    QueryRetrieveResponse,
    QueryAskRequest,
    QueryAskResponse,
    QueryIndexRequest,
    QueryIndexResponse,
    QueryStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

@router.get("/status", response_model=QueryStatusResponse)
def query_status():
    """Lightweight status endpoint for the RAG/query subsystem."""
    from app.core.database import fetch_all
    import os
    from app.core.rag import get_chroma_collection
    
    db_exists = os.path.exists(DB_PATH)
    ticket_count = None
    if db_exists:
        try:
            rows = fetch_all("SELECT COUNT(*) as c FROM tickets")
            if rows:
                ticket_count = rows[0]['c']
        except Exception as e:
            logger.warning(f"API_STATUS_DB: Failed to count tickets. Details: {e}")

    chroma_available = False
    indexed_vector_count = None
    try:
        collection = get_chroma_collection()
        if collection:
            chroma_available = True
            indexed_vector_count = collection.count()
    except Exception as e:
        logger.warning(f"API_STATUS_CHROMA: Failed to load collection. Details: {e}")
        
    index_note = None
    if ticket_count is not None and indexed_vector_count is not None:
        if indexed_vector_count < ticket_count:
            index_note = "partial index"
        elif indexed_vector_count >= ticket_count:
            index_note = "fully indexed"

    status = "ok"
    if not db_exists or ticket_count is None or not chroma_available:
        status = "degraded"

    return QueryStatusResponse(
        service="support-ticket-ai-rag",
        status=status,
        db_path=str(DB_PATH),
        db_exists=db_exists,
        ticket_count=ticket_count,
        chroma_dir=str(CHROMA_DIR),
        collection_name=CHROMA_COLLECTION_NAME,
        chroma_available=chroma_available,
        indexed_vector_count=indexed_vector_count,
        index_note=index_note
    )

@router.post("/retrieve", response_model=QueryRetrieveResponse)
def retrieve_tickets(request: QueryRetrieveRequest):
    """Retrieves relevant support tickets for a given query."""
    if not request.query.strip():
        logger.warning("API_VAL_ERROR: Empty query provided for retrieval.")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        results = retrieve_relevant_tickets(query=request.query, top_k=request.top_k)
        return QueryRetrieveResponse(
            results=results,
            count=len(results)
        )
    except Exception as e:
        logger.error(f"API_RETRIEVE_ERROR: Failed to retrieve tickets. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error during retrieval.")

@router.post("/ask", response_model=QueryAskResponse)
def ask_question(request: QueryAskRequest):
    """Answers a question based on retrieved support tickets."""
    if not request.question.strip():
        logger.warning("API_VAL_ERROR: Empty question provided for ask.")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        response_data = answer_question_with_rag(question=request.question, top_k=request.top_k)
        return QueryAskResponse(
            answer=response_data.get("answer", ""),
            sources=response_data.get("sources", []),
            context_count=response_data.get("context_count", 0),
            error=response_data.get("error"),
            answer_type=response_data.get("answer_type", "rag")
        )
    except Exception as e:
        logger.error(f"API_ASK_ERROR: Failed to generate answer. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error during question answering.")

@router.post("/index", response_model=QueryIndexResponse)
def run_indexing(request: Optional[QueryIndexRequest] = None):
    """Indexes support tickets into the Chroma vector store."""
    limit = request.limit if request else None
    try:
        response_data = index_tickets(limit=limit)
        if response_data.get("status") == "error":
            raise HTTPException(status_code=500, detail=response_data.get("message", "Unknown error during indexing."))
            
        return QueryIndexResponse(
            status=response_data.get("status", "success"),
            indexed=response_data.get("indexed", 0),
            failed=response_data.get("failed", 0),
            message=response_data.get("message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API_INDEX_ERROR: Failed to index tickets. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error during indexing.")
