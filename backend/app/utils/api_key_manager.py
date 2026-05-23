from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from app.models.schemas import APIKey
from app.config import settings

logger = logging.getLogger(__name__)

def get_active_key(db: Session, provider: str) -> str | None:
    """Get the next active key for a provider, un-exhausting keys if 24h passed."""
    # First, un-exhaust keys that are past their time
    now = datetime.now()
    exhausted_keys = db.query(APIKey).filter(
        APIKey.provider == provider,
        APIKey.is_active == 0,
        APIKey.exhausted_until <= now
    ).all()
    
    for key in exhausted_keys:
        key.is_active = 1
        key.exhausted_until = None
    if exhausted_keys:
        db.commit()

    # Get primary key first, then any active key
    key = db.query(APIKey).filter(
        APIKey.provider == provider,
        APIKey.is_active == 1
    ).order_by(APIKey.is_primary.desc()).first()
    
    if key:
        return key.key_value
        
    # Fallback to .env config if no DB key exists
    fallback_map = {
        "fred": settings.fred_api_key,
        "newsapi": settings.news_api_key,
        "guardian": settings.guardian_api_key,
        "nyt": settings.nyt_api_key,
        "openrouter": settings.openrouter_api_key,
        "goldapi": settings.gold_api_key
    }
    return fallback_map.get(provider)

def mark_key_exhausted(db: Session, provider: str, key_value: str):
    """Mark a key as exhausted for 24 hours."""
    key = db.query(APIKey).filter(
        APIKey.provider == provider,
        APIKey.key_value == key_value
    ).first()
    
    if key:
        logger.warning(f"Marking API key for {provider} as exhausted for 24h.")
        key.is_active = 0
        key.exhausted_until = datetime.now() + timedelta(hours=24)
        db.commit()
    else:
        logger.warning(f"Key for {provider} exhausted, but it's not in the DB (likely from .env). Cannot rotate.")
