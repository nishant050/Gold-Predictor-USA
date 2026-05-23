from sqlalchemy.orm import Session
from app.services.news_service import fetch_all_current_news
from app.services.sentiment_service import score_and_store_news
import logging

logger = logging.getLogger(__name__)

def run_daily_news_update(db: Session) -> dict:
    """
    Orchestrate fetching, scoring, and storing daily news.
    """
    logger.info("Starting daily news update orchestrator...")
    news_items = fetch_all_current_news()
    if not news_items:
        logger.info("No news items retrieved.")
        return {"processed": 0, "skipped": 0, "avg_sentiment": 0.0}
        
    result = score_and_store_news(db, news_items)
    logger.info(f"Daily news update complete: {result['processed']} articles processed.")
    return result
