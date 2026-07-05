import pytest
from app.core.analytics import get_dashboard_metrics

def test_get_dashboard_metrics():
    """Test that the dashboard metrics function returns a valid structured dictionary."""
    metrics = get_dashboard_metrics()
    
    assert isinstance(metrics, dict)
    assert metrics.get("total_tickets") == 500
    
    assert isinstance(metrics.get("by_status"), list)
    assert isinstance(metrics.get("by_category"), list)
    
    assert isinstance(metrics.get("average_resolution_time_hrs"), (int, float))
    assert isinstance(metrics.get("top_issues"), list)
