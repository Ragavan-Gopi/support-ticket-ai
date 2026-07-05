from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class QueryRetrieveRequest(BaseModel):
    query: str = Field(..., description="The search query.")
    top_k: int = Field(5, gt=0, description="Number of tickets to retrieve.")

class RetrievedTicket(BaseModel):
    ticket_id: str
    document: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None

class QueryRetrieveResponse(BaseModel):
    results: List[RetrievedTicket]
    count: int

class QueryAskRequest(BaseModel):
    question: str = Field(..., description="The user question.")
    top_k: int = Field(5, gt=0, description="Number of tickets to use as context.")

class QueryAskResponse(BaseModel):
    answer: str
    sources: List[str]
    context_count: int
    error: Optional[str] = None
    answer_type: str = "rag"

class QueryIndexRequest(BaseModel):
    limit: Optional[int] = Field(None, gt=0, description="Limit the number of tickets to index. Omit to index all.")

class QueryIndexResponse(BaseModel):
    status: str
    indexed: int
    failed: Optional[int] = 0
    message: Optional[str] = None

class QueryStatusResponse(BaseModel):
    service: str
    status: str
    db_path: str
    db_exists: bool
    ticket_count: Optional[int] = None
    chroma_dir: str
    collection_name: str
    chroma_available: bool
    indexed_vector_count: Optional[int] = None
    index_note: Optional[str] = None

class AnomalyStatusResponse(BaseModel):
    service: str
    status: str
    db_available: bool
    ticket_count: Optional[int] = None
    anomaly_engine_available: bool

class AnomalyReportResponse(BaseModel):
    volume_spikes: List[Dict[str, Any]] = Field(default_factory=list)
    category_spikes: List[Dict[str, Any]] = Field(default_factory=list)
    priority_anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_outliers: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    recurring_issues: List[Dict[str, Any]] = Field(default_factory=list)
    total_anomalies_found: int
    error: Optional[str] = None

class AnomalySummaryResponse(BaseModel):
    total_anomalies_found: int
    counts_by_category: Dict[str, int]
    counts_by_severity: Dict[str, int]
    top_anomalies: List[Dict[str, Any]]

class AnalyticsDashboardResponse(BaseModel):
    total_tickets: int = 0
    by_status: List[Dict[str, Any]] = Field(default_factory=list)
    by_priority: List[Dict[str, Any]] = Field(default_factory=list)
    by_category: List[Dict[str, Any]] = Field(default_factory=list)
    trend: List[Dict[str, Any]] = Field(default_factory=list)
    average_resolution_time_hrs: float = 0.0
    sla_breaches: Dict[str, Any] = Field(default_factory=dict)
    top_issues: List[Dict[str, Any]] = Field(default_factory=list)
