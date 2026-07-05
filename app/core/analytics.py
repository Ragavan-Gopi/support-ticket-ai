import logging
from typing import List, Dict, Any
from app.core.database import fetch_all

logger = logging.getLogger(__name__)

def get_total_tickets() -> int:
    """Returns the total number of tickets in the database."""
    query = "SELECT count(*) as total FROM tickets"
    result = fetch_all(query)
    if result:
        return result[0]['total']
    return 0

def get_tickets_by_status() -> List[Dict[str, Any]]:
    """Returns ticket counts grouped by status."""
    query = "SELECT status, count(*) as count FROM tickets WHERE status IS NOT NULL GROUP BY status"
    return fetch_all(query)

def get_tickets_by_priority() -> List[Dict[str, Any]]:
    """Returns ticket counts grouped by priority."""
    query = "SELECT priority, count(*) as count FROM tickets WHERE priority IS NOT NULL GROUP BY priority"
    return fetch_all(query)

def get_tickets_by_category() -> List[Dict[str, Any]]:
    """Returns ticket counts grouped by category."""
    query = "SELECT category, count(*) as count FROM tickets WHERE category IS NOT NULL GROUP BY category"
    return fetch_all(query)

def get_ticket_trend() -> List[Dict[str, Any]]:
    """Returns ticket counts grouped by creation date."""
    # Assuming created_at is 'YYYY-MM-DD HH:MM' format, so substr(created_at, 1, 10) extracts 'YYYY-MM-DD'
    query = """
        SELECT substr(created_at, 1, 10) as date, count(*) as count 
        FROM tickets 
        WHERE created_at IS NOT NULL AND created_at != ''
        GROUP BY date 
        ORDER BY date ASC
    """
    return fetch_all(query)

def get_average_resolution_time() -> float:
    """Returns the average resolution time in hours across all resolved tickets."""
    query = "SELECT avg(resolution_time_hrs) as avg_res FROM tickets WHERE resolution_time_hrs IS NOT NULL"
    result = fetch_all(query)
    if result and result[0]['avg_res'] is not None:
        return round(result[0]['avg_res'], 2)
    return 0.0

def get_sla_breach_count() -> Dict[str, Any]:
    """Returns SLA breach metrics, or a default reason if SLA columns don't exist."""
    # The dataset does not have a boolean 'sla_breached' or similar column.
    return {
        "count": 0,
        "reason": "No SLA or breach column exists in the current dataset schema."
    }

def get_top_recurring_issues(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns the top recurring issues based on issue_summary frequency."""
    query = """
        SELECT issue_summary, count(*) as count 
        FROM tickets 
        WHERE issue_summary IS NOT NULL AND issue_summary != ''
        GROUP BY issue_summary 
        ORDER BY count DESC 
        LIMIT ?
    """
    return fetch_all(query, (limit,))

def get_dashboard_metrics() -> Dict[str, Any]:
    """Combines all key analytics metrics into a single dictionary."""
    logger.info("ANOM_ANALYTICS: Gathering dashboard metrics.")
    try:
        metrics = {
            "total_tickets": get_total_tickets(),
            "by_status": get_tickets_by_status(),
            "by_priority": get_tickets_by_priority(),
            "by_category": get_tickets_by_category(),
            "trend": get_ticket_trend(),
            "average_resolution_time_hrs": get_average_resolution_time(),
            "sla_breaches": get_sla_breach_count(),
            "top_issues": get_top_recurring_issues()
        }
        logger.info("ANOM_ANALYTICS: Successfully gathered dashboard metrics.")
        return metrics
    except Exception as e:
        logger.error(f"ANOM_ANALYTICS_ERROR: Failed to gather dashboard metrics. Details: {e}")
        return {}
