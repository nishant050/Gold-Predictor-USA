import json
import os
import sys
import logging
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal, init_db
from app.models.schemas import HistoricalEvent, GoldPrice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_gold_change(db, target_date, days):
    """Fetch the close price roughly 'days' after target_date to compute pct change."""
    start = pd.to_datetime(target_date)
    end = start + pd.Timedelta(days=days + 5) # Pad end date to catch next trading day
    
    prices = db.query(GoldPrice).filter(
        GoldPrice.currency == "USD",
        GoldPrice.date >= start.date(),
        GoldPrice.date <= end.date()
    ).order_by(GoldPrice.date).all()
    
    if len(prices) < 2:
        return None, None
        
    p0 = prices[0].close
    p_end = prices[-1].close
    
    return p0, ((p_end - p0) / p0) * 100

def main():
    init_db()
    db = SessionLocal()
    
    agent_files = [
        "events_war.json",
        "events_crisis.json",
        "events_monetary.json",
        "events_trade.json",
        "events_pandemic.json",
        "events_2024_deepdive.json"
    ]
    
    # Load all existing events to deduplicate by title/date
    existing_events = db.query(HistoricalEvent).all()
    existing_signatures = set()
    for e in existing_events:
        sig = f"{e.event_date}_{e.title.lower().replace(' ', '')}"
        existing_signatures.add(sig)
        
    total_added = 0
    
    for filename in agent_files:
        if not os.path.exists(filename):
            logger.warning(f"File {filename} not found. Skipping.")
            continue
            
        with open(filename, "r", encoding="utf-8") as f:
            try:
                events_list = json.load(f)
            except Exception as e:
                logger.error(f"Failed to parse {filename}: {e}")
                continue
                
        added_from_file = 0
        for ev in events_list:
            try:
                dt = datetime.strptime(ev["event_date"], "%Y-%m-%d").date()
                title = ev["title"]
                sig = f"{dt}_{title.lower().replace(' ', '')}"
                
                if sig in existing_signatures:
                    continue
                    
                p0, c7 = compute_gold_change(db, dt, 7)
                _, c30 = compute_gold_change(db, dt, 30)
                _, c90 = compute_gold_change(db, dt, 90)
                
                new_event = HistoricalEvent(
                    event_date=dt,
                    event_type=ev["event_type"],
                    title=title,
                    description=ev["description"],
                    impact_level=ev["impact_level"],
                    gold_price_at_event=p0,
                    gold_price_change_7d=c7,
                    gold_price_change_30d=c30,
                    gold_price_change_90d=c90,
                    tags=json.dumps(ev.get("tags", [])),
                    source=ev.get("source", "agent_research")
                )
                db.add(new_event)
                existing_signatures.add(sig)
                added_from_file += 1
                total_added += 1
            except Exception as e:
                logger.error(f"Error inserting event {ev.get('title')}: {e}")
                continue
                
        db.commit()
        logger.info(f"Added {added_from_file} new events from {filename}.")
        
    logger.info(f"Total new events added: {total_added}")
    db.close()

if __name__ == "__main__":
    main()
