import logging
from typing import Dict, Any, List, Tuple, Optional
import chromadb

from app.config import CHROMA_DIR, CHROMA_COLLECTION_NAME
from app.core.database import fetch_all
from app.core.llm import generate_embedding, generate_text, LLMError

logger = logging.getLogger(__name__)

# Cache for the Chroma client to avoid re-initializing on every request
_chroma_client = None

def get_chroma_collection():
    """Initializes and returns the ChromaDB collection."""
    global _chroma_client
    try:
        if _chroma_client is None:
            _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            
        return _chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    except Exception as e:
        logger.error(f"RAG_CHROMA_ERROR: Failed to initialize Chroma collection. Details: {e}")
        return None

def build_ticket_document(row: dict) -> Tuple[str, dict]:
    """
    Builds a meaningful text representation of a ticket for embedding,
    and extracts structured metadata.
    """
    # Create a searchable text representation
    doc_text = (
        f"Ticket ID: {row.get('ticket_id', 'Unknown')}. "
        f"Category: {row.get('category', 'Unknown')}. "
        f"Priority: {row.get('priority', 'Unknown')}. "
        f"Status: {row.get('status', 'Unknown')}. "
        f"Issue: {row.get('issue_summary', '')}. "
        f"Created on: {row.get('created_at', '')}."
    )
    
    # Metadata for filtering and context
    metadata = {
        "ticket_id": row.get('ticket_id', ''),
        "category": row.get('category', 'Unknown'),
        "priority": row.get('priority', 'Unknown'),
        "status": row.get('status', 'Unknown'),
        "created_at": row.get('created_at', '')
    }
    
    return doc_text, metadata

def index_tickets(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Reads tickets from SQLite, generates embeddings, and upserts them into ChromaDB.
    """
    logger.info("RAG_INDEX_START: Starting ticket indexing...")
    collection = get_chroma_collection()
    if not collection:
        return {"status": "error", "message": "Failed to access ChromaDB collection."}
        
    query = "SELECT * FROM tickets WHERE ticket_id IS NOT NULL"
    params = ()
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            logger.error("RAG_INDEX_VAL: limit must be a positive integer.")
            return {"status": "error", "message": "limit must be a positive integer."}
        query += " LIMIT ?"
        params = (limit,)
        
    rows = fetch_all(query, params)
    if not rows:
        logger.warning("RAG_INDEX_EMPTY: No tickets found in SQLite to index.")
        return {"status": "success", "indexed": 0, "message": "No tickets found."}
        
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    success_count = 0
    error_count = 0
    
    for row in rows:
        ticket_id = row['ticket_id']
        doc_text, metadata = build_ticket_document(row)
        
        if not doc_text.strip():
            logger.warning(f"RAG_INDEX_SKIP: Empty text for ticket {ticket_id}.")
            error_count += 1
            continue
            
        try:
            # Generate embedding using the LLM wrapper
            emb = generate_embedding(doc_text)
            
            ids.append(ticket_id)
            documents.append(doc_text)
            metadatas.append(metadata)
            embeddings.append(emb)
            
            success_count += 1
        except LLMError as e:
            logger.error(f"RAG_INDEX_LLM_ERROR: Failed embedding ticket {ticket_id}: {e}")
            error_count += 1
            
    # Upsert to ChromaDB in batch
    if ids:
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"RAG_INDEX_SUCCESS: Upserted {success_count} tickets to ChromaDB.")
        except Exception as e:
            logger.error(f"RAG_CHROMA_ERROR: Failed to upsert batch. Details: {e}")
            return {"status": "error", "message": f"ChromaDB upsert failed: {e}"}
            
    return {
        "status": "success",
        "indexed": success_count,
        "failed": error_count
    }

def retrieve_relevant_tickets(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant tickets for a given query from ChromaDB.
    """
    if not query or not query.strip():
        logger.warning("RAG_RETRIEVE_VAL: Empty query provided for retrieval.")
        return []
        
    if not isinstance(top_k, int) or top_k <= 0:
        logger.warning("RAG_RETRIEVE_VAL: top_k must be a positive integer. Defaulting to 5.")
        top_k = 5
        
    collection = get_chroma_collection()
    if not collection:
        return []
        
    try:
        query_embedding = generate_embedding(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        retrieved = []
        if results and results.get("ids") and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                retrieved.append({
                    "ticket_id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
                })
        return retrieved
    except LLMError as e:
        logger.error(f"RAG_RETRIEVE_LLM_ERROR: Failed to embed query. Details: {e}")
        return []
    except Exception as e:
        logger.error(f"RAG_RETRIEVE_ERROR: Failed to query ChromaDB. Details: {e}")
        return []

import re

def route_aggregate_question(question: str) -> Optional[str]:
    """Routes statistical/aggregate questions to deterministic SQL analytics."""
    q_lower = question.lower()
    
    # 1. Total ticket count
    if re.search(r'how many (total )?tickets are there', q_lower) or re.search(r'total number of tickets', q_lower):
        from app.core.analytics import get_total_tickets
        count = get_total_tickets()
        return f"There are {count} tickets."
        
    # 2. Critical unresolved tickets
    if "critical tickets" in q_lower and "unresolved" in q_lower:
        from app.core.database import fetch_all
        rows = fetch_all("SELECT count(*) as c FROM tickets WHERE priority='Critical' AND status NOT IN ('Closed', 'Resolved')")
        return f"There are {rows[0]['c']} critical tickets that are unresolved."
        
    # 3. Escalated tickets
    if "escalated tickets" in q_lower:
        from app.core.database import fetch_all
        rows = fetch_all("SELECT count(*) as c FROM tickets WHERE status='Escalated' OR priority='Escalated'")
        return f"There are {rows[0]['c']} escalated tickets."
        
    # 4. Open tickets
    if "open tickets" in q_lower:
        from app.core.database import fetch_all
        rows = fetch_all("SELECT count(*) as c FROM tickets WHERE status='Open'")
        return f"There are {rows[0]['c']} open tickets."
        
    # 5. Average resolution time
    if "average resolution time" in q_lower:
        from app.core.analytics import get_average_resolution_time
        avg = get_average_resolution_time()
        return f"The average resolution time is {avg} hours."
        
    # 6. Customer rating
    if "average customer rating" in q_lower:
        try:
            from app.core.database import fetch_all
            rows = fetch_all("SELECT agent_id, avg(customer_rating) as avg_rating FROM tickets WHERE customer_rating IS NOT NULL GROUP BY agent_id ORDER BY avg_rating ASC LIMIT 1")
            if rows and rows[0]['avg_rating'] is not None:
                return f"Agent {rows[0]['agent_id']} has the lowest average customer rating of {rows[0]['avg_rating']:.2f}."
            else:
                return "This dataset does not contain customer rating fields, so this cannot be calculated."
        except Exception:
            return "This dataset does not contain customer rating fields, so this cannot be calculated."

    return None

def answer_question_with_rag(question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Answers a user question using hybrid analytics routing or retrieved support tickets.
    """
    logger.info(f"RAG_ANSWER_START: Answering question: '{question}'")
    
    # 0. Hybrid Analytics Routing
    analytics_answer = route_aggregate_question(question)
    if analytics_answer:
        logger.info("RAG_ANSWER_HYBRID: Routed to analytics.")
        return {
            "answer": analytics_answer,
            "sources": ["SQLite analytics"],
            "context_count": 0,
            "answer_type": "analytics"
        }
    
    # 1. Retrieve Context
    retrieved_tickets = retrieve_relevant_tickets(question, top_k)
    
    if not retrieved_tickets:
        logger.info("RAG_ANSWER_NO_CONTEXT: No relevant context found.")
        return {
            "answer": "I don't have enough information from the support tickets to answer your question.",
            "sources": [],
            "context_count": 0,
            "answer_type": "rag"
        }
        
    # 2. Build Prompt with Context
    context_text = "\\n\\n".join([f"- {t['document']}" for t in retrieved_tickets])
    
    system_prompt = (
        "You are a helpful support analytics assistant. "
        "Answer the user's question based strictly on the provided support ticket context. "
        "Do not hallucinate or make up facts. "
        "If the context does not contain the answer, say so clearly."
    )
    
    user_prompt = f"Context:\\n{context_text}\\n\\nQuestion: {question}"
    
    # 3. Generate Answer
    try:
        response_data = generate_text(prompt=user_prompt, system_prompt=system_prompt)
        answer = response_data.get("response", "No answer generated.")
        
        logger.info("RAG_ANSWER_SUCCESS: Successfully generated answer.")
        return {
            "answer": answer.strip(),
            "sources": [t["ticket_id"] for t in retrieved_tickets],
            "context_count": len(retrieved_tickets),
            "answer_type": "rag"
        }
    except LLMError as e:
        logger.error(f"RAG_ANSWER_LLM_ERROR: Failed to generate answer. Details: {e}")
        return {
            "answer": "An error occurred while generating the answer. Please try again later.",
            "sources": [],
            "context_count": 0,
            "error": str(e),
            "answer_type": "rag"
        }
