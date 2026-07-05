import csv
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)

def safe_float(value: str) -> float | None:
    try:
        if not value or not value.strip():
            return None
        return float(value)
    except ValueError:
        return None

def safe_int(value: str) -> int | None:
    try:
        if not value or not value.strip():
            return None
        return int(float(value))
    except ValueError:
        return None

def ingest_csv_to_db(csv_path: str | Path) -> Tuple[int, int, int]:
    """
    Ingests the support tickets CSV into the SQLite database.
    Returns a tuple of (rows_read, rows_inserted_or_updated, rows_skipped).
    """
    path = Path(csv_path)
    
    if not path.exists():
        logger.error(f"ING_CSV_MISSING: The source CSV file was not found at {path}")
        return 0, 0, 0
    
    if path.stat().st_size == 0:
        logger.error("ING_CSV_EMPTY: The source CSV file is empty.")
        return 0, 0, 0

    rows_read = 0
    rows_processed = 0
    rows_skipped = 0

    conn = get_db_connection()
    if not conn:
        logger.error("ING_DB_ERROR: Could not connect to database for ingestion.")
        return 0, 0, 0

    try:
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check for minimum required headers
            if not reader.fieldnames or 'ticket_id' not in reader.fieldnames:
                logger.error("ING_CSV_MALFORMED: Missing required 'ticket_id' column in CSV headers.")
                return 0, 0, 0

            cursor = conn.cursor()
            
            for row in reader:
                rows_read += 1
                
                ticket_id = row.get('ticket_id', '').strip()
                if not ticket_id:
                    logger.warning(f"ING_CSV_SKIP: Skipping row {rows_read} due to missing ticket_id.")
                    rows_skipped += 1
                    continue
                
                created_at = row.get('created_at', '').strip()
                category = row.get('category', '').strip()
                priority = row.get('priority', '').strip()
                status = row.get('status', '').strip()
                response_time = safe_float(row.get('response_time_hrs', ''))
                resolution_time = safe_float(row.get('resolution_time_hrs', ''))
                agent_id = row.get('agent_id', '').strip()
                customer_rating = safe_int(row.get('customer_rating', ''))
                issue_summary = row.get('issue_summary', '').strip()

                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO tickets (
                            ticket_id, created_at, category, priority, status,
                            response_time_hrs, resolution_time_hrs, agent_id,
                            customer_rating, issue_summary
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ticket_id, created_at, category, priority, status,
                        response_time, resolution_time, agent_id,
                        customer_rating, issue_summary
                    ))
                    rows_processed += 1
                except Exception as e:
                    logger.error(f"ING_DB_INSERT_ERROR: Failed to insert ticket {ticket_id}. Details: {e}")
                    rows_skipped += 1

            conn.commit()
            logger.info(f"ING_SUCCESS: Ingestion completed. Read: {rows_read}, Processed: {rows_processed}, Skipped: {rows_skipped}")

    except Exception as e:
        logger.error(f"ING_ERROR: An unexpected error occurred during ingestion. Details: {e}")
        conn.rollback()
    finally:
        conn.close()

    return rows_read, rows_processed, rows_skipped
