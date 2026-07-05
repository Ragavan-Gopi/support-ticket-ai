import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
try:
    TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
except ValueError:
    TIMEOUT = 10

st.set_page_config(page_title="Support Ticket AI", layout="wide")

def fetch_json(endpoint: str, params=None, method="GET", body=None) -> dict:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=body, timeout=TIMEOUT * 3) # Allow more time for LLM
        else:
            response = requests.get(url, params=params, timeout=TIMEOUT)
            
        if not response.ok:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            st.error(f"API Error | Endpoint: {endpoint} | Method: {method.upper()} | Status: {response.status_code} | Detail: {detail}")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"_request_error": "Request timed out while waiting for the backend. Local Ollama generation may take longer. Increase API_TIMEOUT or try a smaller top_k."}
    except requests.exceptions.HTTPError as e:
        return {"_request_error": str(e)}
    except Exception as e:
        st.error(f"Error connecting to backend API: {url} | Method: {method.upper()}")
        return {"_request_error": str(e)}

st.title("Support Ticket AI")
st.markdown("An AI engineering assessment app for support ticket analytics, anomaly detection, and RAG.")

# --- Backend Status ---
st.header("Backend Status")
col1, col2, col3, col4, col5 = st.columns(5)

root_status = fetch_json("/")
health_status = fetch_json("/health/ollama")
query_status = fetch_json("/query/status")
anomalies_status = fetch_json("/anomalies/status")

with col1:
    st.metric("API Root", "Running" if "message" in root_status else "Error")
with col2:
    st.metric("Ollama Service", health_status.get("status", "Error"))
with col3:
    db_count = query_status.get("ticket_count", "N/A")
    st.metric("DB Tickets", db_count)
with col4:
    chroma_count = query_status.get("indexed_vector_count", "N/A")
    note = query_status.get("index_note", "")
    st.metric("Indexed Vectors", chroma_count, delta=note if note == "partial index" else None, delta_color="off")
with col5:
    st.metric("Anomaly Engine", anomalies_status.get("status", "Error").capitalize())

if query_status.get("index_note") == "partial index":
    st.warning("⚠️ Chroma vector store contains a partial index. RAG results may not cover all tickets.")

# --- Analytics Dashboard ---
st.header("Analytics Dashboard")
analytics = fetch_json("/anomalies/analytics")
if "_request_error" not in analytics:
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("Total Tickets", analytics.get("total_tickets", 0))
    ac2.metric("Avg Resolution Time (hrs)", analytics.get("average_resolution_time_hrs", 0))
    sla_breaches = analytics.get("sla_breaches", {})
    ac3.metric("SLA Breaches", sla_breaches.get("count", "N/A"), help=sla_breaches.get("reason"))
    
    st.subheader("Top Recurring Issues")
    top_issues = analytics.get("top_issues", [])
    if top_issues:
        st.table(top_issues)
else:
    st.error("Failed to load analytics.")

# --- Anomaly Dashboard ---
st.header("Anomaly Dashboard")
anomaly_summary = fetch_json("/anomalies/summary")
if "_request_error" not in anomaly_summary:
    st.metric("Total Anomalies Found", anomaly_summary.get("total_anomalies_found", 0))
    
    an1, an2 = st.columns(2)
    with an1:
        st.write("Counts by Severity")
        st.write(anomaly_summary.get("counts_by_severity", {}))
    with an2:
        st.write("Counts by Category")
        st.write(anomaly_summary.get("counts_by_category", {}))
        
    st.subheader("Top Anomalies")
    for anomaly in anomaly_summary.get("top_anomalies", []):
        st.info(f"[{anomaly.get('severity', '').upper()}] {anomaly.get('anomaly_type')}: {anomaly.get('reason')}")
        
    with st.expander("View Full Anomaly Report"):
        report = fetch_json("/anomalies/report")
        if "_request_error" not in report:
            st.json(report)
        else:
            st.error("Failed to load full report.")
else:
    st.error("Failed to load anomaly summary.")

# --- RAG Search ---
st.header("RAG Search (Retrieve)")
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search_query = st.text_input("Search query")
with search_col2:
    search_top_k = st.number_input("Top K (Search)", min_value=1, max_value=20, value=2)

if st.button("Retrieve Tickets"):
    if not search_query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Retrieving..."):
            results = fetch_json("/query/retrieve", method="POST", body={"query": search_query, "top_k": search_top_k})
            if "_request_error" not in results:
                st.success(f"Found {results.get('count', 0)} tickets.")
                for tkt in results.get("results", []):
                    st.markdown(f"**{tkt.get('ticket_id')}** (Score: {tkt.get('distance')})")
                    st.write(tkt.get("document"))
                    st.divider()
            else:
                st.error("Failed to retrieve tickets.")

# --- Ask AI ---
st.header("Ask AI (Analytics + RAG)")
st.caption("Ask questions about the support tickets. Count/statistical questions use SQLite analytics; descriptive questions use RAG.")
ask_col1, ask_col2 = st.columns([3, 1])
with ask_col1:
    ask_question = st.text_input("Ask a question about the support tickets")
with ask_col2:
    ask_top_k = st.number_input("Context size (Top K)", min_value=1, max_value=20, value=3)

if st.button("Generate Answer"):
    if not ask_question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating answer (this may take a few seconds with local Ollama)..."):
            ans_res = fetch_json("/query/ask", method="POST", body={"question": ask_question, "top_k": ask_top_k})
            if "_request_error" not in ans_res:
                if ans_res.get("error"):
                    st.error(ans_res.get("error"))
                else:
                    answer_type = ans_res.get("answer_type", "rag").upper()
                    st.markdown(f"### Answer ({answer_type})")
                    st.write(ans_res.get("answer"))
                    if answer_type == "ANALYTICS":
                        st.markdown("**Source:** SQLite analytics")
                    else:
                        st.markdown(f"**Sources ({ans_res.get('context_count', 0)} tickets):** {', '.join(ans_res.get('sources', []))}")
            else:
                st.error("Failed to connect to Ask AI service.")

# --- Indexing Control ---
with st.expander("Admin: Indexing Control", expanded=False):
    st.warning("Indexing uses the local Ollama embedding model. Large batches will take time.")
    index_limit = st.number_input("Number of tickets to index (Limit)", min_value=1, max_value=500, value=10)
    if st.button("Run Indexing"):
        with st.spinner(f"Indexing up to {index_limit} tickets..."):
            idx_res = fetch_json("/query/index", method="POST", body={"limit": index_limit})
            if "_request_error" not in idx_res:
                if idx_res.get("status") == "success":
                    st.success(f"Successfully indexed {idx_res.get('indexed')} tickets. Failed: {idx_res.get('failed')}")
                else:
                    st.error(f"Indexing failed: {idx_res.get('message')}")
            else:
                st.error("Failed to connect to Indexing service.")
