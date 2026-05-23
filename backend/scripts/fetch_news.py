import logging
import sys
import os

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.services.data_ingestion import run_daily_news_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fetch_news")

def main():
    logger.info("Initializing DB and starting news fetching...")
    init_db()
    
    db = SessionLocal()
    try:
        result = run_daily_news_update(db)
        logger.info("=== News Fetch Summary ===")
        logger.info(f"Processed: {result['processed']}")
        logger.info(f"Skipped (duplicates): {result['skipped']}")
        logger.info(f"Avg Sentiment Score: {result['avg_sentiment']:.4f}")
        logger.info("==========================")
    except Exception as e:
        logger.exception(f"Error during news fetching: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
