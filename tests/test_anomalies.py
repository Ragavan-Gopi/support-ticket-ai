import pytest
from app.core.anomalies import get_anomaly_report

def test_get_anomaly_report():
    """Test that the anomaly report returns all expected categories and valid structure."""
    report = get_anomaly_report()
    
    assert isinstance(report, dict)
    assert "total_anomalies_found" in report
    assert isinstance(report["total_anomalies_found"], int)
    
    expected_categories = [
        "volume_spikes",
        "category_spikes",
        "priority_anomalies",
        "resolution_outliers",
        "escalation_patterns",
        "recurring_issues"
    ]
    
    for cat in expected_categories:
        assert cat in report
        assert isinstance(report[cat], list)
        
    if report.get("resolution_outliers"):
        outlier = report["resolution_outliers"][0]
        assert "severity" in outlier
        assert "reason" in outlier
