import logging
import os
from fastapi import APIRouter, HTTPException

from app.config import DB_PATH
from app.core.analytics import get_dashboard_metrics, get_total_tickets
from app.core.anomalies import get_anomaly_report
from app.core.schemas import (
    AnomalyStatusResponse,
    AnomalyReportResponse,
    AnomalySummaryResponse,
    AnalyticsDashboardResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anomalies", tags=["anomalies"])

@router.get("/status", response_model=AnomalyStatusResponse)
def get_status():
    """Lightweight status endpoint for the anomalies subsystem."""
    db_available = os.path.exists(DB_PATH)
    ticket_count = None
    anomaly_engine_available = False
    
    if db_available:
        try:
            from app.core.database import fetch_all
            rows = fetch_all("SELECT COUNT(*) as c FROM tickets")
            if rows:
                ticket_count = rows[0]['c']
                anomaly_engine_available = True
        except Exception as e:
            logger.warning(f"API_STATUS_ANOMALY: Failed to access DB or anomaly engine. Details: {e}")

    status = "ok"
    if not db_available or ticket_count is None or not anomaly_engine_available:
        status = "degraded"

    return AnomalyStatusResponse(
        service="support-ticket-ai-anomalies",
        status=status,
        db_available=db_available,
        ticket_count=ticket_count,
        anomaly_engine_available=anomaly_engine_available
    )

@router.get("/report", response_model=AnomalyReportResponse)
def get_report():
    """Returns the full anomaly report."""
    try:
        report = get_anomaly_report()
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        return AnomalyReportResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API_ANOM_ERROR: Failed to generate report. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error generating anomaly report.")

@router.get("/summary", response_model=AnomalySummaryResponse)
def get_summary():
    """Returns a compact summary derived from get_anomaly_report()."""
    try:
        report = get_anomaly_report()
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
            
        counts_by_category = {
            "volume_spikes": len(report.get("volume_spikes", [])),
            "category_spikes": len(report.get("category_spikes", [])),
            "priority_anomalies": len(report.get("priority_anomalies", [])),
            "resolution_outliers": len(report.get("resolution_outliers", [])),
            "escalation_patterns": len(report.get("escalation_patterns", [])),
            "recurring_issues": len(report.get("recurring_issues", []))
        }
        
        all_anomalies = []
        for cat, items in report.items():
            if isinstance(items, list):
                all_anomalies.extend(items)
                
        counts_by_severity = {"high": 0, "medium": 0, "low": 0}
        for item in all_anomalies:
            sev = item.get("severity", "low").lower()
            if sev in counts_by_severity:
                counts_by_severity[sev] += 1
            else:
                counts_by_severity[sev] = 1
                
        # Top anomalies: prioritize high severity
        def sev_score(anomaly):
            s = anomaly.get("severity", "low").lower()
            return {"high": 3, "medium": 2, "low": 1}.get(s, 0)
            
        all_anomalies.sort(key=sev_score, reverse=True)
        top_anomalies = all_anomalies[:3]
        
        return AnomalySummaryResponse(
            total_anomalies_found=report.get("total_anomalies_found", 0),
            counts_by_category=counts_by_category,
            counts_by_severity=counts_by_severity,
            top_anomalies=top_anomalies
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API_ANOM_ERROR: Failed to generate summary. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error generating anomaly summary.")

@router.get("/analytics", response_model=AnalyticsDashboardResponse)
def get_analytics():
    """Returns dashboard analytics."""
    try:
        metrics = get_dashboard_metrics()
        if not metrics:
            raise HTTPException(status_code=500, detail="Failed to fetch dashboard metrics.")
        return AnalyticsDashboardResponse(**metrics)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API_ANOM_ERROR: Failed to fetch analytics. Details: {e}")
        raise HTTPException(status_code=500, detail="Internal error fetching analytics.")
