import logging
import sys
from pathlib import Path

# Add project root to sys.path so we can import from app
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import DB_PATH, DATA_DIR
from app.core.database import init_db
from app.core.ingestion import ingest_csv_to_db

# Configure simple logging for the script output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    csv_path = DATA_DIR / "support_tickets.csv"
    
    logger.info("Starting ingestion script...")
    logger.info(f"Using CSV source: {csv_path}")
    logger.info(f"Using DB destination: {DB_PATH}")
    
    if not init_db():
        logger.error("Failed to initialize database. Aborting ingestion.")
        sys.exit(1)
        
    rows_read, rows_processed, rows_skipped = ingest_csv_to_db(csv_path)
    
    logger.info("=== Ingestion Summary ===")
    logger.info(f"Rows read from CSV: {rows_read}")
    logger.info(f"Rows inserted/updated: {rows_processed}")
    logger.info(f"Rows skipped: {rows_skipped}")
    
    if rows_read > 0 and rows_processed > 0:
        logger.info("Final Status: SUCCESS")
    else:
        logger.warning("Final Status: COMPLETED WITH ISSUES (or empty source)")

if __name__ == "__main__":
    main()
