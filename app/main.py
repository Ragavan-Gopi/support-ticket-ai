from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_query import router as query_router
from app.api.routes_anomalies import router as anomalies_router


app = FastAPI(
    title="Support Ticket AI",
    description="AI engineering assessment project for support ticket analytics, anomaly detection, and RAG.",
    version="0.1.0",
)


app.include_router(health_router)
app.include_router(query_router)
app.include_router(anomalies_router)


@app.get("/")
def root():
    return {
        "message": "Support Ticket AI API is running"
    }