import requests
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.schemas import GoldPrice
from app.utils.api_key_manager import get_active_key, mark_key_exhausted
import logging
import time

logger = logging.getLogger(__name__)

def fetch_gold_prices(db: Session, start_date: str = None) -> int:
    """
    Fetch gold prices from GoldAPI.io.
    """
    max_retries = 3
    retry_count = 0
    success = False
    data = None
    
    url = "https://www.goldapi.io/api/XAU/USD"
    
    while retry_count < max_retries and not success:
        api_key = get_active_key(db, "goldapi")
        if not api_key:
            logger.error("No active GoldAPI key available.")
            return 0
            
        headers = {
            "x-access-token": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code in (429, 403, 402):
                logger.warning(f"GoldAPI key exhausted: {response.status_code}")
                mark_key_exhausted(db, "goldapi", api_key)
                retry_count += 1
                time.sleep(1)
                continue
                
            response.raise_for_status()
            data = response.json()
            success = True
            
        except Exception as e:
            logger.error(f"Error fetching from GoldAPI: {e}")
            break
            
    if not success or not data:
        return 0
        
    # Process GoldAPI response
    price = data.get("price")
    op = data.get("open_price", price)
    hi = data.get("high_price", price)
    lo = data.get("low_price", price)
    
    # Store in DB
    existing_date = db.query(GoldPrice).filter(
        GoldPrice.date == datetime.now().date(),
        GoldPrice.currency == "USD"
    ).first()
    
    if not existing_date:
        gold_price = GoldPrice(
            date=datetime.now().date(),
            open=op,
            high=hi,
            low=lo,
            close=price,
            currency="USD",
            source="goldapi"
        )
        db.add(gold_price)
        db.commit()
        return 1
    return 0
