import logging
import sys
import os
import json
from datetime import datetime, date, timedelta

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.schemas import HistoricalEvent
from scripts.seed_historical_events import get_nearest_price

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_1996_events")

EVENTS_DATA_1996 = [
    {
        "event_date": "1996-12-05",
        "event_type": "monetary_policy",
        "title": "Alan Greenspan 'Irrational Exuberance' Speech",
        "description": "Fed Chairman warns about overvalued stock markets, causing a brief global market drop.",
        "impact_level": 2,
        "tags": ["fed", "markets", "speech", "greenspan"],
        "source": "manual_curation"
    },
    {
        "event_date": "1997-07-02",
        "event_type": "economic_crisis",
        "title": "Asian Financial Crisis Begins",
        "description": "Thailand devalues the Baht, triggering a massive financial contagion across Asia.",
        "impact_level": 4,
        "tags": ["asia", "crisis", "currency", "contagion"],
        "source": "manual_curation"
    },
    {
        "event_date": "1998-08-17",
        "event_type": "economic_crisis",
        "title": "Russian Financial Crisis (Ruble Default)",
        "description": "Russia devalues the ruble and defaults on its debt, sending shockwaves through global markets.",
        "impact_level": 5,
        "tags": ["russia", "default", "crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "1998-09-23",
        "event_type": "economic_crisis",
        "title": "LTCM Bailout Organized by Fed",
        "description": "Long-Term Capital Management hedge fund fails, prompting a $3.6B Fed-orchestrated bailout.",
        "impact_level": 4,
        "tags": ["hedge_fund", "bailout", "fed", "crisis"],
        "source": "manual_curation"
    },
    {
        "event_date": "1999-01-01",
        "event_type": "monetary_policy",
        "title": "Euro Currency Officially Introduced",
        "description": "The Euro is established as an electronic currency for banking and financial markets in 11 nations.",
        "impact_level": 3,
        "tags": ["euro", "currency", "europe"],
        "source": "manual_curation"
    },
    {
        "event_date": "1999-05-07",
        "event_type": "war",
        "title": "US Bombs Chinese Embassy in Belgrade",
        "description": "NATO bombs Chinese embassy during the Kosovo war, spiking US-China tensions.",
        "impact_level": 3,
        "tags": ["war", "nato", "china", "us", "kosovo"],
        "source": "manual_curation"
    },
    {
        "event_date": "2000-03-10",
        "event_type": "market_crash",
        "title": "NASDAQ Peaks - Dot-com Bubble Burst Begins",
        "description": "The NASDAQ reaches its dot-com peak before plunging, destroying trillions in tech wealth.",
        "impact_level": 5,
        "tags": ["dotcom", "bubble", "crash", "stocks"],
        "source": "manual_curation"
    },
    {
        "event_date": "2000-11-07",
        "event_type": "election",
        "title": "Bush v. Gore Election Dispute",
        "description": "US Presidential election results in a recount crisis that lasts for over a month.",
        "impact_level": 3,
        "tags": ["election", "us", "politics", "uncertainty"],
        "source": "manual_curation"
    },
    {
        "event_date": "2001-01-03",
        "event_type": "monetary_policy",
        "title": "Fed Emergency Rate Cut for Dot-com Crash",
        "description": "Federal Reserve surprisingly cuts rates by 50bps to stop the bleeding in tech stocks.",
        "impact_level": 4,
        "tags": ["fed", "rate_cut", "emergency"],
        "source": "manual_curation"
    },
    {
        "event_date": "2003-02-05",
        "event_type": "geopolitics",
        "title": "Colin Powell UN Iraq Speech",
        "description": "US Secretary of State presents case for invading Iraq to the UN, cementing path to war.",
        "impact_level": 3,
        "tags": ["iraq", "un", "us", "geopolitics", "war_prelude"],
        "source": "manual_curation"
    }
]

def seed_1996_events():
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        
        for ev in EVENTS_DATA_1996:
            # Deduplicate
            existing = db.query(HistoricalEvent).filter(HistoricalEvent.title == ev["title"]).first()
            if existing:
                existing.event_date = datetime.strptime(ev["event_date"], "%Y-%m-%d").date()
                existing.description = ev["description"]
                existing.tags = json.dumps(ev["tags"])
                updated += 1
            else:
                new_event = HistoricalEvent(
                    event_date=datetime.strptime(ev["event_date"], "%Y-%m-%d").date(),
                    event_type=ev["event_type"],
                    title=ev["title"],
                    description=ev["description"],
                    impact_level=ev["impact_level"],
                    tags=json.dumps(ev["tags"]),
                    source=ev["source"]
                )
                db.add(new_event)
                inserted += 1
                
        db.commit()
        logger.info(f"Seeded {inserted} 1996-era events, updated {updated}.")
        
        # Recalculate correlations for these events
        events = db.query(HistoricalEvent).filter(HistoricalEvent.event_date < '2004-01-01').all()
        for event in events:
            price_at_event = get_nearest_price(db, event.event_date, direction='before')
            if not price_at_event: continue
                
            price_7d = get_nearest_price(db, event.event_date + timedelta(days=7), direction='before')
            price_30d = get_nearest_price(db, event.event_date + timedelta(days=30), direction='before')
            
            event.gold_price_at_event = price_at_event
            if price_7d:
                event.gold_price_change_7d = ((price_7d - price_at_event) / price_at_event) * 100
            if price_30d:
                event.gold_price_change_30d = ((price_30d - price_at_event) / price_at_event) * 100
                
        db.commit()
        logger.info("Correlations calculated.")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_1996_events()
