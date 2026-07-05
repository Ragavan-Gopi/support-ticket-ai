import logging
import statistics
from typing import List, Dict, Any
from app.core.database import fetch_all
from app.core.analytics import get_total_tickets

logger = logging.getLogger(__name__)

def detect_volume_spikes(threshold_z: float = 2.0) -> List[Dict[str, Any]]:
    """Detects days where ticket volume is unusually high (z-score > threshold)."""
    anomalies = []
    query = """
        SELECT substr(created_at, 1, 10) as date, count(*) as count 
        FROM tickets 
        WHERE created_at IS NOT NULL AND created_at != ''
        GROUP BY date 
        ORDER BY date ASC
    """
    rows = fetch_all(query)
    if len(rows) < 3:
        return anomalies  # Not enough data

    counts = [row['count'] for row in rows]
    mean_count = statistics.mean(counts)
    stdev_count = statistics.stdev(counts) if len(counts) > 1 else 0.0

    if stdev_count == 0:
        return anomalies

    for row in rows:
        z_score = (row['count'] - mean_count) / stdev_count
        if z_score > threshold_z:
            anomalies.append({
                "anomaly_type": "high_volume_day",
                "severity": "medium",
                "metric": row['count'],
                "reason": f"Ticket volume {row['count']} is significantly higher than average {mean_count:.1f}.",
                "date": row['date']
            })
    return anomalies

def detect_category_spikes(threshold_z: float = 2.0) -> List[Dict[str, Any]]:
    """Detects unusual spikes in specific categories on a given day."""
    anomalies = []
    query = """
        SELECT substr(created_at, 1, 10) as date, category, count(*) as count 
        FROM tickets 
        WHERE created_at IS NOT NULL AND category IS NOT NULL
        GROUP BY date, category 
        ORDER BY date ASC
    """
    rows = fetch_all(query)
    if not rows:
        return anomalies
    
    # Group by category to find category-specific stats
    category_counts = {}
    for row in rows:
        cat = row['category']
        if cat not in category_counts:
            category_counts[cat] = []
        category_counts[cat].append(row)
        
    for cat, daily_records in category_counts.items():
        if len(daily_records) < 3:
            continue
        counts = [r['count'] for r in daily_records]
        mean_c = statistics.mean(counts)
        stdev_c = statistics.stdev(counts) if len(counts) > 1 else 0.0
        
        if stdev_c == 0:
            continue
            
        for r in daily_records:
            z_score = (r['count'] - mean_c) / stdev_c
            if z_score > threshold_z:
                anomalies.append({
                    "anomaly_type": "category_spike",
                    "severity": "medium",
                    "metric": r['count'],
                    "reason": f"Category '{cat}' volume {r['count']} is significantly higher than its average {mean_c:.1f}.",
                    "date": r['date'],
                    "category": cat
                })
    return anomalies

def detect_priority_anomalies(critical_threshold_pct: float = 0.20) -> List[Dict[str, Any]]:
    """Detects if high/critical priority tickets form an unusually large percentage of the total."""
    anomalies = []
    total = get_total_tickets()
    if total == 0:
        return anomalies
        
    query = "SELECT priority, count(*) as count FROM tickets WHERE priority IS NOT NULL GROUP BY priority"
    rows = fetch_all(query)
    
    for row in rows:
        pct = row['count'] / total
        # Check if 'Critical' priority exceeds the threshold
        if row['priority'].lower() == 'critical' and pct > critical_threshold_pct:
            anomalies.append({
                "anomaly_type": "high_critical_volume",
                "severity": "high",
                "metric": f"{pct*100:.1f}%",
                "reason": f"Critical priority tickets make up {pct*100:.1f}% of total, exceeding {critical_threshold_pct*100}% threshold.",
                "priority": row['priority']
            })
    return anomalies

def detect_resolution_outliers(threshold_z: float = 3.0, limit: int = 5) -> List[Dict[str, Any]]:
    """Detects specific tickets with unusually high resolution times (z-score > threshold)."""
    anomalies = []
    query = "SELECT ticket_id, category, resolution_time_hrs FROM tickets WHERE resolution_time_hrs IS NOT NULL"
    rows = fetch_all(query)
    if len(rows) < 3:
        return anomalies
        
    times = [row['resolution_time_hrs'] for row in rows]
    mean_time = statistics.mean(times)
    stdev_time = statistics.stdev(times) if len(times) > 1 else 0.0
    
    if stdev_time == 0:
        return anomalies
        
    # Find outliers and sort them by highest time
    outliers = []
    for row in rows:
        z_score = (row['resolution_time_hrs'] - mean_time) / stdev_time
        if z_score > threshold_z:
            outliers.append(row)
            
    outliers.sort(key=lambda x: x['resolution_time_hrs'], reverse=True)
    
    for row in outliers[:limit]:
        # Calculate an explainable severity based on the multiple of the mean
        ratio = row['resolution_time_hrs'] / mean_time if mean_time > 0 else 0
        if ratio >= 5.0:
            severity = "high"
        elif ratio >= 3.0:
            severity = "medium"
        else:
            severity = "low"
            
        anomalies.append({
            "anomaly_type": "resolution_time_outlier",
            "severity": severity,
            "metric": row['resolution_time_hrs'],
            "reason": f"Resolution time {row['resolution_time_hrs']} hrs is {ratio:.1f}x the average ({mean_time:.1f} hrs).",
            "ticket_id": row['ticket_id'],
            "category": row['category']
        })
    return anomalies

def detect_escalation_patterns(escalation_threshold_pct: float = 0.15) -> List[Dict[str, Any]]:
    """Detects if escalated tickets form an unusually large percentage of the total."""
    anomalies = []
    total = get_total_tickets()
    if total == 0:
        return anomalies
        
    query = "SELECT status, count(*) as count FROM tickets WHERE status IS NOT NULL GROUP BY status"
    rows = fetch_all(query)
    
    for row in rows:
        pct = row['count'] / total
        if row['status'].lower() == 'escalated' and pct > escalation_threshold_pct:
            anomalies.append({
                "anomaly_type": "high_escalation_rate",
                "severity": "high",
                "metric": f"{pct*100:.1f}%",
                "reason": f"Escalated tickets make up {pct*100:.1f}% of total, exceeding {escalation_threshold_pct*100}% threshold.",
                "status": row['status']
            })
    return anomalies

def detect_recurring_issue_spikes(issue_threshold_pct: float = 0.05) -> List[Dict[str, Any]]:
    """Detects specific issue summaries that appear very frequently."""
    anomalies = []
    total = get_total_tickets()
    if total == 0:
        return anomalies
        
    query = "SELECT issue_summary, count(*) as count FROM tickets WHERE issue_summary IS NOT NULL AND issue_summary != '' GROUP BY issue_summary"
    rows = fetch_all(query)
    
    for row in rows:
        pct = row['count'] / total
        if pct > issue_threshold_pct:
            anomalies.append({
                "anomaly_type": "recurring_issue_spike",
                "severity": "medium",
                "metric": f"{pct*100:.1f}%",
                "reason": f"Issue '{row['issue_summary']}' makes up {pct*100:.1f}% of total tickets ({row['count']} tickets).",
                "issue_summary": row['issue_summary']
            })
    return anomalies

def get_anomaly_report() -> Dict[str, Any]:
    """Runs all anomaly detections and returns a combined report."""
    logger.info("ANOM_DETECT: Running anomaly detection pipeline.")
    try:
        report = {
            "volume_spikes": detect_volume_spikes(),
            "category_spikes": detect_category_spikes(),
            "priority_anomalies": detect_priority_anomalies(),
            "resolution_outliers": detect_resolution_outliers(),
            "escalation_patterns": detect_escalation_patterns(),
            "recurring_issues": detect_recurring_issue_spikes()
        }
        
        # Count total anomalies found
        total_anomalies = sum(len(items) for items in report.values())
        report["total_anomalies_found"] = total_anomalies
        
        logger.info(f"ANOM_SUCCESS: Anomaly detection completed. Found {total_anomalies} anomalies.")
        return report
    except Exception as e:
        logger.error(f"ANOM_ERROR: Failed to run anomaly detection. Details: {e}")
        return {"total_anomalies_found": 0, "error": str(e)}
